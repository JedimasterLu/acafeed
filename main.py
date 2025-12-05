import os
import argparse
import pprint
import toml
import acafeed
from acafeed import FeedConfig


def init_command():
    """Initialize AcaFeed configuration"""
    print("Initializing AcaFeed...")


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
        "-s", "--search", help="Search feed sources by keyword"
    )

    args = parser.parse_args()

    # Handle commands
    if args.command == "init":
        init_command()
    elif args.command == "config":
        # Handle config command later
        pass


if __name__ == "__main__":
    main()
