from __future__ import annotations

import re


class IssueSummarizer:
    """Extractive summarizer — first sentence or truncated description."""

    def summarize(self, description: str, title: str | None = None, max_len: int = 160) -> str:
        if title and len(title.strip()) >= 10:
            return title.strip()[:max_len]

        text = description.strip()
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if sentences and len(sentences[0]) >= 20:
            summary = sentences[0]
        else:
            summary = text

        if len(summary) > max_len:
            return summary[: max_len - 3].rstrip() + "..."
        return summary


issue_summarizer = IssueSummarizer()
