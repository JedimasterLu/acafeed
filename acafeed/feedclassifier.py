"""
Feed Classifier: 使用训练好的 SciBERT 模型对论文标题进行多标签分类
"""
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from .abbr_table import arxiv_abbr


@dataclass
class PredictionResult:
    title: str
    predicted_labels: list[PredictionLabel]
    top_labels: list[PredictionLabel] | None = None


@dataclass
class PredictionLabel:
    label: str
    score: float


class FeedClassifier:
    """论文分类器，使用预训练的 SciBERT 模型"""
    
    def __init__(
        self, 
        checkpoint_path: str | None = None,
        tokenizer_name: str = "allenai/scibert_scivocab_uncased",
        max_length: int = 64,
        threshold: float = 0.4,
        device: str | None = None
    ):
        # 设置设备
        if device is None:
            if torch.backends.mps.is_available():
                self.device = torch.device("mps")
            elif torch.cuda.is_available():
                self.device = torch.device("cuda")
            else:
                self.device = torch.device("cpu")
        else:
            self.device = torch.device(device)
        
        # 设置参数
        self.max_length = max_length
        self.threshold = threshold
        
        # 加载 tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        
        # 设置 checkpoint 路径
        if checkpoint_path is None:
            # 默认使用 model/model1_best.pt
            project_root = Path(__file__).parent.parent
            ckpt_path = project_root / "model" / "model1_best.pt"
        else:
            ckpt_path = Path(checkpoint_path)
        
        if not ckpt_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {ckpt_path}")
        
        # 加载 checkpoint
        ckpt = torch.load(ckpt_path, map_location=self.device, weights_only=False)
        
        # 从 checkpoint 中获取模型配置
        model_state = ckpt["model_state"]
        
        # 推断标签数量（从分类器层的权重维度）
        # 通常在 classifier.weight 或 bert.pooler.dense.weight 后的分类层
        classifier_keys = [k for k in model_state.keys() if "classifier" in k and "weight" in k]
        if classifier_keys:
            num_labels = model_state[classifier_keys[0]].shape[0]
        else:
            raise ValueError("Cannot infer num_labels from checkpoint")
        
        # 初始化模型（使用相同的架构）
        self.model = AutoModelForSequenceClassification.from_pretrained(
            tokenizer_name,
            num_labels=num_labels,
            problem_type="multi_label_classification",
            ignore_mismatched_sizes=True,
        )
        
        # 加载模型权重
        self.model.load_state_dict(model_state)
        self.model.to(self.device)
        self.model.eval()
        
        # 从 checkpoint 中加载 id2label 映射
        if "id2label" in ckpt:
            # 直接从 checkpoint 读取
            self.id2label = ckpt["id2label"]
        elif hasattr(self.model.config, "id2label") and self.model.config.id2label:
            # 尝试从模型配置读取
            self.id2label = self.model.config.id2label
        else:
            # 使用数字标签作为后备方案
            self.id2label = {i: f"label_{i}" for i in range(num_labels)}
    
    def _sigmoid(self, x):
        """Sigmoid 函数"""
        return 1 / (1 + np.exp(-x))
    
    def predict(
        self, 
        titles: list[str],
        return_all_scores: bool = False,
        top_k: int = 5
    ) -> list[PredictionResult]:

        if not titles:
            return []
        
        # Tokenize
        encoded = self.tokenizer(
            titles,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.max_length
        )
        
        # 移到设备
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        
        # 推理
        with torch.no_grad():
            outputs = self.model(**encoded)
            logits = outputs.logits.cpu().numpy()
        
        # 应用 sigmoid
        probs = self._sigmoid(logits)
        
        # 构建结果
        results = []
        for i, (title, prob) in enumerate(zip(titles, probs)):
            # 预测标签 (超过阈值)
            pred_indices = np.where(prob > self.threshold)[0]
            predicted_labels = [
                    PredictionLabel(
                        label=self.id2label[int(idx)],
                        score=float(prob[idx])
                    )
                    for idx in pred_indices
                ]
            # 按分数降序排序
            predicted_labels.sort(key=lambda x: x.score, reverse=True)
            
            result = PredictionResult(
                title=title,
                predicted_labels=predicted_labels,
            )
            
            # 如果需要，添加 top-k 标签
            if return_all_scores:
                top_indices = np.argsort(prob)[::-1][:top_k]
                top_labels = [
                    PredictionLabel(
                        label=self.id2label[int(idx)],
                        score=float(prob[idx])
                    )
                    for idx in top_indices
                ]
                result.top_labels = top_labels
            
            results.append(result)
        
        return results
    
    def judge(
            self,
            classes: list[str],
            results: list[PredictionResult]
        ) -> list[bool]:
        """Judge whether the labels in results belongs to user's interest.

        Supports prefix operators for flexible matching:
        - No prefix (OR): At least one of these classes should appear
        - '+' prefix (AND): This class must appear
        - '-' prefix (NOT): This class must not appear

        Args:
            classes (list[str]): User's interested classes with optional prefixes.
                Examples: ["Machine Learning", "+Computer Vision", "-Biology"]
            results (list[PredictionResult]): The prediction results to judge.

        Returns:
            list[bool]: A list of booleans indicating whether each result is relevant.
        """
        abbr_table = arxiv_abbr()
        
        # Parse classes into different categories
        or_classes = []
        and_classes = []
        not_classes = []
        
        for cls in classes:
            if cls.startswith('+'):
                class_name = cls[1:]
                if class_name not in abbr_table.values():
                    raise ValueError(f"Class '{class_name}' is not a valid label in arxiv abbreviation table.")
                and_classes.append(class_name)
            elif cls.startswith('-'):
                class_name = cls[1:]
                if class_name not in abbr_table.values():
                    raise ValueError(f"Class '{class_name}' is not a valid label in arxiv abbreviation table.")
                not_classes.append(class_name)
            else:
                if cls not in abbr_table.values():
                    raise ValueError(f"Class '{cls}' is not a valid label in arxiv abbreviation table.")
                or_classes.append(cls)
        
        judgments = []
        for result in results:
            assert result.top_labels is not None, \
                "Top labels are required for judgment. Please set return_all_scores=True in predict()."
            
            top_label_names = [abbr_table[label.label] for label in result.top_labels]
            
            # Check NOT conditions (must not contain any)
            has_excluded = any(not_class in top_label_names for not_class in not_classes)
            if has_excluded:
                judgments.append(False)
                continue
            
            # Check AND conditions (must contain all)
            has_all_required = all(and_class in top_label_names for and_class in and_classes)
            if not has_all_required:
                judgments.append(False)
                continue
            
            # Check OR conditions (must contain at least one, if any OR classes specified)
            if or_classes:
                has_any_or = any(or_class in top_label_names for or_class in or_classes)
                judgments.append(has_any_or)
            else:
                # If no OR classes, and we passed AND/NOT checks, it's relevant
                judgments.append(True)
        
        return judgments
