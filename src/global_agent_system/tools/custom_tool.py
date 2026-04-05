from html import unescape
from re import sub as re_sub
from typing import Type

import feedparser
from pydantic import BaseModel, Field

from crewai.tools import BaseTool


def _strip_html(text: str) -> str:
    if not text:
        return ""
    plain = re_sub(r"<[^>]+>", " ", text)
    plain = unescape(plain)
    return " ".join(plain.split())


class RSSFeedToolInput(BaseModel):
    """Input schema for RSSFeedTool."""

    rss_url: str = Field(..., description="Full URL of the RSS or Atom feed to fetch and parse.")


class RSSFeedTool(BaseTool):
    name: str = "rss_feed_reader"
    description: str = (
        "Fetches an RSS or Atom feed from a URL and returns the latest entries "
        "with title, link, published date, and a short summary (max 300 characters each)."
    )
    args_schema: Type[BaseModel] = RSSFeedToolInput

    def _run(self, rss_url: str) -> str:
        parsed = feedparser.parse(rss_url)
        if getattr(parsed, "bozo", False) and not getattr(parsed, "entries", None):
            err = getattr(parsed, "bozo_exception", None)
            return f"Failed to parse feed: {err or 'unknown error'}"

        entries = list(getattr(parsed, "entries", []) or [])[:10]
        if not entries:
            return "No entries found in this feed."

        lines: list[str] = []
        for i, entry in enumerate(entries, start=1):
            title = entry.get("title", "(no title)")
            link = entry.get("link", "")
            published = entry.get("published") or entry.get("updated") or "(no date)"
            raw_summary = entry.get("summary") or entry.get("description") or ""
            if not raw_summary:
                content = entry.get("content")
                if isinstance(content, list) and content:
                    first = content[0]
                    if isinstance(first, dict):
                        raw_summary = first.get("value", "")
            summary = _strip_html(str(raw_summary))
            if len(summary) > 300:
                summary = summary[:297] + "..."

            lines.append(f"--- Entry {i} ---")
            lines.append(f"Title: {title}")
            lines.append(f"Link: {link}")
            lines.append(f"Published: {published}")
            lines.append(f"Summary: {summary}")
            lines.append("")

        return "\n".join(lines).strip()


class MyCustomToolInput(BaseModel):
    """Input schema for MyCustomTool."""

    argument: str = Field(..., description="Description of the argument.")


class MyCustomTool(BaseTool):
    name: str = "Name of my tool"
    description: str = "Clear description for what this tool is useful for, your agent will need this information to use it."
    args_schema: Type[BaseModel] = MyCustomToolInput

    def _run(self, argument: str) -> str:
        # Implementation goes here
        return "this is an example of a tool output, ignore it and move along."
