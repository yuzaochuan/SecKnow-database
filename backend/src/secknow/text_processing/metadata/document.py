from __future__ import annotations

"""文档级元数据构建。"""

from pathlib import Path

from ..config import SUPPORTED_EXTS
from ..schemas.document import LoadedDocument
from .hashing import build_doc_id


def build_loaded_document(file_path: str | Path) -> LoadedDocument:
    """从文件路径构造文档元数据。"""
    path = Path(file_path).expanduser().resolve()
    stat = path.stat()
    extension = path.suffix.lower()

    return LoadedDocument(
        source_path=str(path),
        filename=path.name,
        extension=extension,
        file_type=SUPPORTED_EXTS.get(extension, "text"),
        size_bytes=int(stat.st_size),
        mtime=int(stat.st_mtime),
        doc_id=build_doc_id(path),
    )
