import os
import argparse
import pprint
import acafeed


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="AcaFeed Command Line Interface")
    parser.add_argument('--add-feed', type=str, help='Add a new feed URL')
    parser.add_argument('--list-feeds', action='store_true', help='List all feeds')
    parser.add_argument('--fetch', type=str, help='Fetch and update all feeds')
    args = parser.parse_args()

    db = acafeed.FeedSource()
    if os.path.exists("feeds.pkl"):
        db.load("feeds.pkl")

    if args.add_feed:
        # Logic to add a new feed]
        db.add(link=args.add_feed, name="Nature Materials")

    if args.list_feeds:
        # Logic to list all feeds
        db.pprint()
        print(f"Total feeds: {len(db._feeds)}")
    
    if args.fetch:
        # Logic to fetch and update all feeds
        pprint.pprint(db.fetch(args.fetch))
    
    db.save("feeds.pkl")


if __name__ == "__main__":
    main()
