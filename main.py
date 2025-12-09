import os
import subprocess
import argparse
import pprint
import toml
import acafeed
from acafeed import FeedConfig, arxiv_abbr, FeedSource, FeedEmitter, FeedClassifier

config = None

def init_command():
    """Initialize AcaFeed configuration"""
    # 1. Create default configuration if not exists
    global config
    config = setup_config()

    # 2. If no url in config, print a message
    if not config.sources:
        print("Please add rss source by: acafeed source -a <url (name) | key words>")
    
    # 3. Set interests
    if not config.interests:
        print("Please add interested categories by: acafeed interest -a <category name>")

    # 4. Get git repo url
    result = subprocess.run(
        ['git', 'config', '--get', 'remote.origin.url'],
        capture_output=True,
        text=True,
        cwd='/Users/jylu/Projects/acafeed'
    )
    repo_url = result.stdout.strip()
    config.repo = repo_url 
    
    with open("config.toml", "w") as f:
        toml.dump(config.to_dict(), f)


def setup_config() -> FeedConfig:
    # If there is no config.toml file in the current directory, create a default one
    if not os.path.exists("config.toml"):
        config = acafeed.FeedConfig()
        config_data = config.to_dict()
        with open("config.toml", "w") as f:
            toml.dump(config_data, f)
    else:
        # Load the existing configuration from config.toml
        with open("config.toml", "r") as f:
            config_data = toml.load(f)
            config = FeedConfig(**config_data)
    return config


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="AcaFeed Command Line Interface")
    parser.add_argument(
        "-v", "--version", action="version", version="AcaFeed 1.0.0"
    )

    subparsers = parser.add_subparsers(title='commands', dest="command")

    subparsers.add_parser("init", help="Initialize AcaFeed")

    subparsers.add_parser("fetch", help="Update feed entries")

    interest_cfg = subparsers.add_parser("interest", help="Manage interests")
    interest_cfg.add_argument(
        "-a", "--add", help="Add a new interest category"
    )
    interest_cfg.add_argument(
        "-r", "--remove", help="Remove an interest category"
    )
    interest_cfg.add_argument(
        "-l", "--list", action="store_true", help="List all interest categories"
    )
    interest_cfg.add_argument(
        "-L", "--list-all", help="List all available arXiv categories", action="store_true"
    )

    sp_cfg = subparsers.add_parser("config", help="Manipulate configuration")
    sp_cfg.add_argument(
        "-l", "--list", action="store_true", help="List current configuration"
    )
    sp_cfg.add_argument(
        "-s", "--set", nargs=2, metavar=("KEY", "VALUE"), help="Set configuration key to value"
    )

    sp_source = subparsers.add_parser("source", help="Manage feed sources")
    sp_source.add_argument(
        "-a", "--add", help="Add a new feed source URL"
    )
    sp_source.add_argument(
        "-r", "--remove", help="Remove a feed source URL"
    )
    sp_source.add_argument(
        "-l", "--list", action="store_true", help="List all feed sources"
    )
    sp_source.add_argument(
        "-s", "--search", nargs=1, help="Search feed sources by keyword"
    )

    args = parser.parse_args()

    # Handle commands
    if args.command == "init":
        init_command()
    elif args.command == "config":
        config = None
        with open("config.toml", "r") as f:
            config_data = toml.load(f)
            config = FeedConfig(**config_data)
        assert isinstance(config, FeedConfig)
        if args.list:
            pprint.pprint(config)
        elif args.set:
            key, value = args.set
            if hasattr(config, key):
                setattr(config, key, type(getattr(config, key))(value))
                with open("config.toml", "w") as f:
                    toml.dump(config.to_dict(), f)
            else:
                print(f"Configuration key '{key}' does not exist.")
    elif args.command == "source":
        feed_source = FeedSource()
        config = None
        with open("config.toml", "r") as f:
            config_data = toml.load(f)
            config = FeedConfig(**config_data)
        assert isinstance(config, FeedConfig)
        if args.add:
            # Check if names are included if URL
            if "http" in args.add:
                if "(" not in args.add:
                    print("Please provide a name for the feed source in the format: <url> (name)")
                    return
            config.sources.append(args.add)
            with open("config.toml", "w") as f:
                toml.dump(config.to_dict(), f)
        elif args.remove:
            if args.remove in config.sources:
                config.sources.remove(args.remove)
                with open("config.toml", "w") as f:
                    toml.dump(config.to_dict(), f)
            else:
                print(f"Source URL '{args.remove}' not found in configuration.")
        elif args.list:
            for url in config.sources:
                print(url)
        elif args.search:
            keyword = args.search[0].lower()
            for name, url in feed_source.common_feeds.items():
                if keyword in name.lower():
                    print(f"{name}: {url}")
    elif args.command == "interest":
        config = None
        with open("config.toml", "r") as f:
            config_data = toml.load(f)
            config = FeedConfig(**config_data)
        assert isinstance(config, FeedConfig)
        if args.add:
            if args.add not in config.interests:
                config.interests.append(args.add)
                with open("config.toml", "w") as f:
                    toml.dump(config.to_dict(), f)
            else:
                print(f"Interest '{args.add}' already exists.")
        elif args.remove:
            if args.remove in config.interests:
                config.interests.remove(args.remove)
                with open("config.toml", "w") as f:
                    toml.dump(config.to_dict(), f)
            else:
                print(f"Interest '{args.remove}' not found in configuration.")
        elif args.list:
            for interest in config.interests:
                print(interest)
        elif args.list_all:
            abbr_table = arxiv_abbr()
            for abbr, full_name in abbr_table.items():
                print(f"{abbr}: {full_name}")
    elif args.command == "fetch":
        with open("config.toml", "r") as f:
            config_data = toml.load(f)
            config = FeedConfig(**config_data)
        assert isinstance(config, FeedConfig)
        feed_source = FeedSource()
        for s in config.sources:
            if "http" in s:
                # The source is a URL (name)
                feed_name = s.split(" (")[-1].rstrip(")")
                feed_url = s.split(" (")[0]
                feed_source.add(feed_url, name=feed_name)
            else:
                feed_source.add_by_title(s)
        entries = feed_source.fetch_all()
        classifier = FeedClassifier(
            checkpoint_path=config.checkpoint_path,
            tokenizer_name=config.tokenizer_name,
            max_length=config.max_title_length,
            threshold=config.threshold,
            device=config.device
        )
        entry_titles: list[str] = [str(entry.title) for entry in entries]
        results = classifier.predict(entry_titles, return_all_scores=True, top_k=5)
        judgments = classifier.judge(classes=config.interests, results=results)
        filtered_entries = [entry for i, entry in enumerate(entries) if judgments[i]]

        emitter = FeedEmitter(
            entries=filtered_entries,
            title=config.feed_title,
            home_page=config.repo,
            description=config.description,
            language=config.language
        )
        emitter.generate_and_push()


if __name__ == "__main__":
    main()
