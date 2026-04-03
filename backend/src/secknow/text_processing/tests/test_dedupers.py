from __future__ import annotations

from secknow.text_processing.dedupers.router import dedup_chunks


def test_exact_dedup() -> None:
    """exact 去重应保留首次出现的 chunk。"""
    chunks = ["A", "B", "A", "C", "B"]
    assert dedup_chunks(chunks, strategy="exact") == ["A", "B", "C"]
