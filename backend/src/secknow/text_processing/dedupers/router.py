from __future__ import annotations

"""去重路由。"""

from ..config import DEFAULT_DEDUP_STRATEGY
from ..exceptions import TextProcessingError
from .exact import dedup_exact


def dedup_chunks(chunks: list[str], strategy: str = DEFAULT_DEDUP_STRATEGY) -> list[str]:
    """根据策略执行去重，目前 Phase 1 仅支持 exact。"""
    strategy = (strategy or DEFAULT_DEDUP_STRATEGY).strip().lower()
    if strategy != "exact":
        raise TextProcessingError(f"暂不支持的去重策略: {strategy}")
    return dedup_exact(chunks)
