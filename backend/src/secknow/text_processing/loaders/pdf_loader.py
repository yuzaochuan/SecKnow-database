from __future__ import annotations

"""PDF 加载器。"""

from pathlib import Path

import pdfplumber

from ..exceptions import DocumentLoadError


def load_pdf(file_path: str | Path) -> str:
    """提取 PDF 文本，按页拼接。"""
    path = Path(file_path)
    try:
        with pdfplumber.open(path) as pdf:
            pages = [(page.extract_text() or "") for page in pdf.pages]
    except Exception as exc:  # pragma: no cover - 三方库抛错类型不稳定
        raise DocumentLoadError(f"读取 PDF 失败: {path}") from exc

    return "\n".join(page.strip() for page in pages if page.strip())
