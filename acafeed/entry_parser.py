"""
entry_parser.py
----------------
Standardizes RSS entries returned by feedparser
into a consistent Python dict format suitable
for ML classification.
"""

from typing import List, Dict, Any
import datetime
from dateutil import parser as date_parser
import re
from html import unescape
from typing import Optional


def _safe_get(entry: dict, key: str, default="N/A"):
    """Safely extract an RSS field, falling back if missing."""
    value = entry.get(key)
    return value if value not in (None, "") else default


def clean_summary(raw_summary: str) -> str:
    if not raw_summary:
        return ""

    text = raw_summary

    # Remove HTML tags
    text = re.sub(r"<.*?>", " ", text)

    # Remove "Published online: <date>"
    text = re.sub(
        r"Published online:\s*\d{1,2}\s+\w+\s+\d{4}", 
        "", 
        text, 
        flags=re.IGNORECASE
    )

    # Remove DOI patterns
    text = re.sub(
        r"doi:\s*\S+", 
        "", 
        text, 
        flags=re.IGNORECASE
    )

    # Collapse whitespace
    text = re.sub(r"\s{2,}", " ", text).strip()

    return text



def _parse_date(date_str: Optional[str]):
    """Convert RSS date string to datetime.datetime (if possible)."""
    if not date_str:
        return None
    try:
        return date_parser.parse(date_str)
    except Exception:
        return None


def _parse_authors(entry: dict) -> str:
    """Normalize authors: list → string; fallback to 'Unknown'."""
    if "authors" in entry and entry["authors"]:
        names = [a.get("name", "").strip() for a in entry["authors"]]
        names = [n for n in names if n]
        return ", ".join(names) if names else "Unknown"

    if entry.get("author"):
        return entry["author"]

    return "Unknown"
    


def clean_html(text: str) -> str:
    """Remove HTML tags and unescape HTML entities."""
    if not text:
        return ""
    text = unescape(text)
    # remove tags like <p>...</p>
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def parse_entries(feed_data) -> List[Dict[str, Any]]:
    """
    Convert feedparser.FeedParserDict to normalized entries.

    Parameters
    ----------
    feed_data : feedparser.FeedParserDict

    Returns
    -------
    List[dict] : cleaned, standardized entries
    """

    parsed_entries = []

    for item in feed_data.entries:
        entry = {}

        # ---- Basic fields ----
        entry["title"] = _safe_get(item, "title", "Untitled Paper")

        # Get and clean summary
        raw_summary = _safe_get(item, "summary", "")
        cleaned_summary = clean_summary(raw_summary)
        if not cleaned_summary:
            cleaned_summary = "No abstract available"
        entry["summary"] = cleaned_summary

        entry["link"] = _safe_get(item, "link", "N/A")
        entry["authors"] = _parse_authors(item)

        # ---- Publication date ----
        pub_raw = (
            _safe_get(item, "published", None)
            or _safe_get(item, "updated", None)
        )
        entry["published"] = _parse_date(pub_raw)

        # ---- Source (journal name) ----
        entry["source"] = feed_data.feed.get("title", "Unknown Source")

        # ---- Text used for ML classification ----
        entry["text_for_classification"] = " ".join(
            part for part in [entry["title"], entry["summary"]] if part
        )

        parsed_entries.append(entry)

    return parsed_entries

