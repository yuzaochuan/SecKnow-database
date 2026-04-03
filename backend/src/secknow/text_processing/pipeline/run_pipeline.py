from __future__ import annotations

"""最小闭环流水线：文件 -> 文本 -> 分块 -> 去重 -> 编码 -> records。"""

from pathlib import Path

from secknow.vector_store.models import ChunkRecord, RecordType, ZoneId

from ..chunkers.router import chunk_text
from ..cleaners.basic import basic_clean
from ..config import (
    DEFAULT_CHUNK_STRATEGY,
    DEFAULT_DEDUP_STRATEGY,
    get_chunk_max_tokens,
    get_chunk_overlap,
)
from ..dedupers.router import dedup_chunks
from ..encoders.factory import build_embedder
from ..exceptions import ChunkingError
from ..loaders.router import load_document_text
from ..metadata.chunk import build_chunk_metadata
from ..metadata.document import build_loaded_document
from ..schemas.chunk import EncodedChunk, TextChunk
from ..schemas.document import RawDocument
from ..schemas.pipeline_result import PipelineResult


class DocumentTextPipeline:
    """4.1 对外主入口类。"""

    def __init__(
        self,
        *,
        chunk_strategy: str = DEFAULT_CHUNK_STRATEGY,
        dedup_strategy: str = DEFAULT_DEDUP_STRATEGY,
        max_tokens: int | None = None,
        overlap: int | None = None,
        embedding_mode: str | None = None,
        embedding_model: str | None = None,
        embedding_dim: int | None = None,
        embedder=None,
    ):
        self.chunk_strategy = chunk_strategy
        self.dedup_strategy = dedup_strategy
        self.max_tokens = max_tokens or get_chunk_max_tokens()
        self.overlap = get_chunk_overlap() if overlap is None else overlap
        self.embedder = embedder or build_embedder(
            mode=embedding_mode,
            model_name=embedding_model,
            dim=embedding_dim,
        )

    def process_file(
        self,
        file_path: str | Path,
        *,
        zone_id: ZoneId,
        record_type: RecordType = "knowledge",
        language: str | None = None,
        return_result: bool = False,
    ) -> list[ChunkRecord] | PipelineResult:
        """处理文件并输出可直接给 4.3 upsert 的 records。"""
        path = Path(file_path)
        raw_text = load_document_text(path)
        clean_text = basic_clean(raw_text)

        if not clean_text:
            raise ChunkingError(f"清洗后文本为空，无法分块: {path}")

        loaded_document = build_loaded_document(path)
        chunk_texts = chunk_text(
            clean_text,
            strategy=self.chunk_strategy,
            max_tokens=self.max_tokens,
            overlap=self.overlap,
        )
        original_chunks = [
            TextChunk(text=chunk, chunk_index=i, chunk_count=len(chunk_texts))
            for i, chunk in enumerate(chunk_texts)
        ]

        deduped_texts = dedup_chunks(chunk_texts, strategy=self.dedup_strategy)
        deduped_chunks = [
            TextChunk(text=chunk, chunk_index=i, chunk_count=len(deduped_texts))
            for i, chunk in enumerate(deduped_texts)
        ]

        vectors = self.embedder.encode(deduped_texts)
        encoded_chunks = [
            EncodedChunk(text_chunk=text_chunk, vector=vector)
            for text_chunk, vector in zip(deduped_chunks, vectors, strict=False)
        ]

        records: list[ChunkRecord] = []
        for item in encoded_chunks:
            metadata = build_chunk_metadata(
                document=loaded_document,
                zone_id=zone_id,
                chunk_index=item.text_chunk.chunk_index,
                chunk_count=item.text_chunk.chunk_count,
                chunk_text=item.text_chunk.text,
                record_type=record_type,
                language=language,
            )
            records.append(
                ChunkRecord(
                    text=item.text_chunk.text,
                    vector=item.vector,
                    metadata=metadata,
                )
            )

        if not return_result:
            return records

        return PipelineResult(
            raw_document=RawDocument(source_path=str(path), text=raw_text),
            loaded_document=loaded_document,
            chunks=original_chunks,
            deduped_chunks=deduped_chunks,
            encoded_chunks=encoded_chunks,
            records=records,
        )

    def process_text(
        self,
        text: str,
        *,
        source_path: str,
        zone_id: ZoneId,
        record_type: RecordType = "knowledge",
        language: str | None = None,
        return_result: bool = False,
    ) -> list[ChunkRecord] | PipelineResult:
        """处理原始文本，便于在 API/测试中绕过文件加载阶段。"""
        temp_path = Path(source_path)
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_text(text, encoding="utf-8")
        return self.process_file(
            temp_path,
            zone_id=zone_id,
            record_type=record_type,
            language=language,
            return_result=return_result,
        )


def run_pipeline(
    file_path: str | Path,
    *,
    zone_id: ZoneId,
    record_type: RecordType = "knowledge",
    language: str | None = None,
    pipeline: DocumentTextPipeline | None = None,
) -> list[ChunkRecord]:
    """函数式入口：直接返回 records。"""
    current = pipeline or DocumentTextPipeline()
    return current.process_file(
        file_path,
        zone_id=zone_id,
        record_type=record_type,
        language=language,
        return_result=False,
    )
