"""
token_manager.py
Handles Gemini free-tier token limits and usage tracking.

Free tier limits (as of 2025):
  gemini-1.5-flash : 1,000,000 tokens/min  |  1,500 req/day
  gemini-1.5-pro   :    32,000 tokens/min  |     50 req/day
  gemini-2.0-flash : 1,000,000 tokens/min  |  1,500 req/day

We track a rolling per-session budget to stay safe.
"""

import time
from dataclasses import dataclass, field
from typing import List


# ── Per-model conservative daily caps (tokens) ───────────────────────────────
MODEL_CAPS = {
    "gemini-1.5-flash": 800_000,   # conservative vs 1M/min (daily usage guard)
    "gemini-1.5-pro":   100_000,   # conservative (50 req/day @ ~2k tokens each)
    "gemini-2.0-flash": 800_000,
}

# Avg tokens per image + question (rough estimate for planning)
AVG_TOKENS_PER_QUESTION = 1_200   # image ≈ 500 + prompt ≈ 400 + answer ≈ 300


@dataclass
class UsageRecord:
    timestamp: float
    input_tokens: int
    output_tokens: int


class TokenManager:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model_name = model_name
        self.daily_cap = MODEL_CAPS.get(model_name, 500_000)
        self.records: List[UsageRecord] = []
        self.window_start = time.time()

    #  Core tracking 
    def track_usage(self, input_tokens: int, output_tokens: int) -> None:
        self.records.append(
            UsageRecord(
                timestamp=time.time(),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        )

    def total_used(self) -> int:
        return sum(r.input_tokens + r.output_tokens for r in self.records)

    # Stats
    def get_usage_stats(self):
        used = self.total_used()
        limit = self.daily_cap
        pct = (used / limit) * 100 if limit > 0 else 0
        return used, limit, pct

    def estimate_remaining_questions(self) -> int:
        used = self.total_used()
        remaining_tokens = self.daily_cap - used
        return max(0, int(remaining_tokens / AVG_TOKENS_PER_QUESTION))

    def is_near_limit(self, threshold: float = 0.85) -> bool:
        _, _, pct = self.get_usage_stats()
        return pct >= threshold * 100


    def compress_history(self, messages: list) -> list:
        """
        When token usage > 70%, trim the in-memory chat history to the last
        2 Q&A pairs so the context window stays small.
        Returns the (modified in place) list.
        """
        if len(messages) > 6:
            # Keep only last 4 messages (2 Q&A pairs)
            del messages[:-4]
        return messages

    # Rate-limit sleep helper 
    @staticmethod
    def safe_sleep_on_rate_limit(seconds: int = 30) -> None:
        time.sleep(seconds)

    # Summary string 
    def summary(self) -> str:
        used, limit, pct = self.get_usage_stats()
        remaining = self.estimate_remaining_questions()
        return (
            f"Model: {self.model_name} | "
            f"Used: {used:,}/{limit:,} tokens ({pct:.1f}%) | "
            f"~{remaining} questions left"
        )