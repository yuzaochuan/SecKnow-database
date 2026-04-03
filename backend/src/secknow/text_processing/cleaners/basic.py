from __future__ import annotations

"""基础文本清洗逻辑。"""

import re

# 保留制表符与换行，其余常见控制字符统一清理。
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def basic_clean(text: str) -> str:
    """执行最小清洗：统一换行、清理控制字符、移除空白行。"""
    if not text:
        return ""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = _CONTROL_CHAR_RE.sub("", normalized)

    cleaned_lines: list[str] = []
    for line in normalized.split("\n"):
        stripped = line.strip()
        if stripped:
            cleaned_lines.append(stripped)

    return "\n".join(cleaned_lines).strip()
