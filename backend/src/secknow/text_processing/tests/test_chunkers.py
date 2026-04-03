from __future__ import annotations

from secknow.text_processing.chunkers.router import chunk_text


def test_fixed_window_chunking() -> None:
    """fixed_window 应按窗口切分文本。"""
    text = " ".join([f"token{i}" for i in range(20)])
    chunks = chunk_text(text, strategy="fixed_window", max_tokens=6, overlap=2)
    assert len(chunks) >= 3
    assert all(chunk for chunk in chunks)


def test_hybrid_chunking() -> None:
    """hybrid 应支持段落聚合与切分。"""
    text = "第一段内容\n第二段内容\n第三段内容"
    chunks = chunk_text(text, strategy="hybrid", max_tokens=10, overlap=2)
    assert len(chunks) >= 1
    assert all(isinstance(chunk, str) for chunk in chunks)
