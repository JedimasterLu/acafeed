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


def _safe_get(entry: dict, key: str, default="N/A"):
    """Safely extract an RSS field, falling back if missing."""
    value = entry.get(key)
    return value if value not in (None, "") else default


from typing import Optional

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

        entry["title"] = _safe_get(item, "title", "Untitled Paper")
        entry["summary"] = _safe_get(item, "summary", "No abstract available")
        entry["link"] = _safe_get(item, "link", "N/A")
        entry["authors"] = _parse_authors(item)

        # publication date: published > updated > None
        pub_raw = (
            _safe_get(item, "published", None)
            or _safe_get(item, "updated", None)
        )
        entry["published"] = _parse_date(pub_raw)

        # source (journal name)
        entry["source"] = feed_data.feed.get("title", "Unknown Source")

        # cleanup summary text formatting
        entry["summary"] = entry["summary"].replace("\n", " ").strip()

        parsed_entries.append(entry)

    return parsed_entries


