from __future__ import annotations

"""分块路由。"""

from ..config import (
    DEFAULT_CHUNK_MAX_TOKENS,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_STRATEGY,
)
from ..exceptions import ChunkingError
from .fixed_window import chunk_fixed_window, chunk_hybrid


_SUPPORTED = {"fixed_window", "hybrid"}


def chunk_text(
    text: str,
    strategy: str = DEFAULT_CHUNK_STRATEGY,
    max_tokens: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    """根据策略执行分块。"""
    strategy = (strategy or DEFAULT_CHUNK_STRATEGY).strip().lower()
    max_tokens = max_tokens or DEFAULT_CHUNK_MAX_TOKENS
    overlap = DEFAULT_CHUNK_OVERLAP if overlap is None else overlap

    if strategy not in _SUPPORTED:
        raise ChunkingError(f"暂不支持的分块策略: {strategy}")

    if strategy == "fixed_window":
        return chunk_fixed_window(text=text, max_tokens=max_tokens, overlap=overlap)
    return chunk_hybrid(text=text, max_tokens=max_tokens, overlap=overlap)
