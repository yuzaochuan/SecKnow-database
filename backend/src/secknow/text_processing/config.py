from __future__ import annotations

"""4.1 文本处理模块的基础配置。"""

import os

# 支持的文件扩展名到业务文件类型的映射。
SUPPORTED_EXTS: dict[str, str] = {
    ".txt": "text",
    ".md": "markdown",
    ".markdown": "markdown",
    ".pdf": "pdf",
    ".docx": "docx",
    ".py": "code",
    ".js": "code",
    ".ts": "code",
    ".java": "code",
    ".go": "code",
    ".c": "code",
    ".cpp": "code",
    ".h": "code",
    ".hpp": "code",
    ".json": "text",
    ".yaml": "text",
    ".yml": "text",
    ".toml": "text",
    ".ini": "text",
    ".cfg": "text",
    ".log": "text",
}

# 默认 embedding 约定：与 README 的 Phase 1 契约保持一致。
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_EMBEDDING_DIM = 384
DEFAULT_EMBEDDING_MODE = "sbert"

DEFAULT_CHUNK_STRATEGY = "hybrid"
DEFAULT_DEDUP_STRATEGY = "exact"
DEFAULT_CHUNK_MAX_TOKENS = 300
DEFAULT_CHUNK_OVERLAP = 50


def get_embedding_mode() -> str:
    """读取 embedding 模式：`sbert` 或 `fake`。"""
    return os.getenv("EMBEDDING_MODE", DEFAULT_EMBEDDING_MODE).strip().lower()


def get_embedding_model() -> str:
    """读取 embedding 模型名。"""
    return os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL).strip()


def get_embedding_dim() -> int:
    """读取 embedding 维度，异常值自动回退到默认值。"""
    raw = os.getenv("EMBEDDING_DIM", str(DEFAULT_EMBEDDING_DIM)).strip()
    try:
        dim = int(raw)
    except ValueError:
        return DEFAULT_EMBEDDING_DIM
    return dim if dim > 0 else DEFAULT_EMBEDDING_DIM


def get_chunk_max_tokens() -> int:
    """读取分块最大 token 数。"""
    raw = os.getenv("CHUNK_MAX_TOKENS", str(DEFAULT_CHUNK_MAX_TOKENS)).strip()
    try:
        val = int(raw)
    except ValueError:
        return DEFAULT_CHUNK_MAX_TOKENS
    return val if val > 0 else DEFAULT_CHUNK_MAX_TOKENS


def get_chunk_overlap() -> int:
    """读取分块 overlap。"""
    raw = os.getenv("CHUNK_OVERLAP", str(DEFAULT_CHUNK_OVERLAP)).strip()
    try:
        val = int(raw)
    except ValueError:
        return DEFAULT_CHUNK_OVERLAP
    return max(0, val)
