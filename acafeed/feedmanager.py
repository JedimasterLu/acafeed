"""
This module defines the feedsource class, which is the main class for the feedsource package.
It creates a dataframe to store the rss feed links and history data.
It provides methods to add, remove, and update rss feed links,
as well as to fetch and parse the rss feeds.
It also provides slots for the later AI classification module.
"""
import datetime
from dataclasses import dataclass
import pickle
import feedparser


# Dataclass feed
@dataclass
class Feed:
    link: str
    name: str
    add_time: datetime.datetime
    last_updated: datetime.datetime

    def __post_init__(self):
        """Check the inputs are valid."""
        # Verify the link is a valid URL
        if not isinstance(self.link, str):
            raise TypeError("link must be a string")
        if not isinstance(self.name, str):
            raise TypeError("name must be a string")
        if not isinstance(self.add_time, datetime.datetime):
            raise TypeError("add_time must be a datetime.datetime")
        if not isinstance(self.last_updated, datetime.datetime):
            raise TypeError("last_updated must be a datetime.datetime")
        sample = feedparser.parse(self.link)
        if sample.status == 301:
            print(f"Warning: The link {self.link} is redirected (301). Please check if the link is correct.")
        elif sample.status == 410:
            raise ValueError(f"The link {self.link} is gone (410). Please check if the link is correct.")


class FeedSource:
    """
    The feedsource class is the main class for the feedsource package.
    It creates a dataframe to store the rss feed links and history data.
    It provides methods to add, remove, and update rss feed links,
    as well as to fetch and parse the rss feeds.
    It also provides slots for the later AI classification module.
    """

    def __init__(self):
        """
        Initializes the feedsource class with an empty dataframe.
        The dataframe has columns for the rss feed link, title, description,
        last updated time, and history data.
        """
        self._feeds: list[Feed] = []
        self._feed_names: list[str] = []
    
    def add(self, link: str, name: str):
        """Adds a new RSS feed to the list.

        Args:
            link (str): The URL of the RSS feed.
            name (str): A user-defined name for the feed.

        Raises:
            ValueError: If the link is gone (410).
        """
        # Check if the feed name is already in the list
        if name in self._feed_names:
            print(f"The feed name {name} is already in use. Please choose a different name.")
            return
        # Add the new feed
        now = datetime.datetime.now()
        new_feed = Feed(link=link, name=name, add_time=now, last_updated=now)
        self._feeds.append(new_feed)
        self._feed_names.append(name)
        print(f"The feed {name} has been added.")
    
    def remove(self, name: str):
        """Removes an RSS feed from the list by its name.

        Args:
            name (str): The user-defined name of the feed to remove.
        """
        for i, feed in enumerate(self._feeds):
            if feed.name == name:
                self._feeds.pop(i)
                self._feed_names.remove(name)
                print(f"The feed {name} has been removed.")
                return
        print(f"The feed {name} was not found in the list.")

    def change(
            self,
            name: str,
            new_link: str | None = None,
            new_name: str | None = None,
        ):
        """Changes the link or name of an existing RSS feed.

        Args:
            name (str): The current name of the feed to change.
            new_link (str | None, optional): The new link for the feed. Defaults to None.
            new_name (str | None, optional): The new name for the feed. Defaults to None.
        """
        if new_link is None and new_name is None:
            print("No changes specified.")
            return
        for feed in self._feeds:
            if feed.name == name:
                if new_link is not None:
                    feed.link = new_link
                if new_name is not None:
                    # Check if the new name is already in use
                    if new_name in self._feed_names:
                        print(f"The feed name {new_name} is already in use. \
                              Please choose a different name.")
                        return
                    feed.name = new_name
                    self._feed_names.remove(name)
                    self._feed_names.append(new_name)
                print(f"The feed {name} has been updated.")
                return
            
    def search(self, keyword: str) -> list[Feed]:
        """Searches for feeds by a keyword in their name.

        Args:
            keyword (str): The keyword to search for in feed names.

        Returns:
            list[Feed]: A list of feeds that match the keyword.
        """
        results = [feed for feed in self._feeds if keyword.lower() in feed.name.lower()]
        return results
    
    def pprint(self, name: str | None = None):
        """Prints the details of a feed by its name.

        Args:
            name (str | None): The user-defined name of the feed to print.
                If None, prints all feeds. Defaults to None.
        """
        if name is None:
            for feed in self._feeds:
                print(f"Feed Name: {feed.name}")
                print(f"Feed Link: {feed.link}")
                print(f"Added On: {feed.add_time}")
                print(f"Last Updated: {feed.last_updated}")
                print("-" * 20)
        else:
            for feed in self._feeds:
                if feed.name == name:
                    print(f"Feed Name: {feed.name}")
                    print(f"Feed Link: {feed.link}")
                    print(f"Added On: {feed.add_time}")
                    print(f"Last Updated: {feed.last_updated}")
                    return
            print(f"The feed {name} was not found in the list.")
    
    def load(self, filepath: str):
        """Loads the feed list from a pickle file.

        Args:
            filepath (str): The path to the pickle file.
        """
        try:
            with open(filepath, "rb") as f:
                self._feeds = pickle.load(f)
            self._feed_names = [feed.name for feed in self._feeds]
            print(f"Feed list loaded from {filepath}.")
        except FileNotFoundError:
            print(f"The file {filepath} was not found.")
        except Exception as e:
            print(f"An error occurred while loading the file: {e}")
    
    def save(self, filepath: str):
        """Saves the feed list to a pickle file.

        Args:
            filepath (str): The path to the pickle file.
        """
        try:
            with open(filepath, "wb") as f:
                pickle.dump(self._feeds, f)
            print(f"Feed list saved to {filepath}.")
        except Exception as e:
            print(f"An error occurred while saving the file: {e}")
    
    def fetch(self, name: str) -> feedparser.FeedParserDict | None:
        """Fetches and parses the RSS feed by its name.

        Args:
            name (str): The user-defined name of the feed to fetch.

        Returns:
            feedparser.FeedParserDict | None: The parsed feed data, or None if not found.
        """
        if name not in self._feed_names:
            print(f"The feed {name} was not found in the list.")
            return None
        for feed in self._feeds:
            if feed.name == name:
                parsed_feed = feedparser.parse(feed.link)
                return parsed_feed
        return None
