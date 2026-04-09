from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.src.secknow.vector_store.models import (
    ChunkMetadata, ChunkRecord, generate_chunk_id, ZoneId, RecordType
)


def test_chunk_metadata_required_fields():
    """测试ChunkMetadata必填字段约束"""
    # 缺少必填字段应该抛出ValidationError
    with pytest.raises(ValidationError):
        ChunkMetadata(
            # 缺少doc_id
            zone_id="cyber",
            filename="test.md",
            source_path="/path/test.md",
            extension=".md",
            chunk_index=0,
            chunk_count=1,
            char_len=10,
            content_hash="hash",
            mtime=1234567890,
            size_bytes=100,
            file_type="markdown"
        )
    
    with pytest.raises(ValidationError):
        ChunkMetadata(
            doc_id="test",
            # 缺少zone_id
            filename="test.md",
            source_path="/path/test.md",
            extension=".md",
            chunk_index=0,
            chunk_count=1,
            char_len=10,
            content_hash="hash",
            mtime=1234567890,
            size_bytes=100,
            file_type="markdown"
        )


def test_generate_chunk_id_stability():
    """测试generate_chunk_id()的稳定性"""
    metadata = ChunkMetadata(
        doc_id="test_doc",
        zone_id="cyber",
        filename="test.md",
        source_path="/path/test.md",
        extension=".md",
        chunk_index=0,
        chunk_count=1,
        char_len=10,
        content_hash="test_hash",
        mtime=1234567890,
        size_bytes=100,
        file_type="markdown"
    )
    
    # 多次调用应该返回相同的结果
    id1 = generate_chunk_id(metadata)
    id2 = generate_chunk_id(metadata)
    assert id1 == id2
    assert len(id1) == 40  # SHA1 hash长度


def test_zone_id_bounds():
    """测试zone_id边界值"""
    # 有效的zone_id
    valid_zones: list[ZoneId] = ["cyber", "ai", "crypto"]
    for zone in valid_zones:
        metadata = ChunkMetadata(
            doc_id="test",
            zone_id=zone,
            filename="test.md",
            source_path="/path/test.md",
            extension=".md",
            chunk_index=0,
            chunk_count=1,
            char_len=10,
            content_hash="hash",
            mtime=1234567890,
            size_bytes=100,
            file_type="markdown"
        )
        assert metadata.zone_id == zone
    
    # 无效的zone_id应该抛出ValidationError
    with pytest.raises(ValidationError):
        ChunkMetadata(
            doc_id="test",
            zone_id="invalid_zone",  # 无效的zone_id
            filename="test.md",
            source_path="/path/test.md",
            extension=".md",
            chunk_index=0,
            chunk_count=1,
            char_len=10,
            content_hash="hash",
            mtime=1234567890,
            size_bytes=100,
            file_type="markdown"
        )


def test_record_type_bounds():
    """测试record_type边界值"""
    # 有效的record_type
    valid_types: list[RecordType] = ["knowledge", "baseline"]
    for record_type in valid_types:
        metadata = ChunkMetadata(
            doc_id="test",
            zone_id="cyber",
            filename="test.md",
            source_path="/path/test.md",
            extension=".md",
            chunk_index=0,
            chunk_count=1,
            char_len=10,
            content_hash="hash",
            mtime=1234567890,
            size_bytes=100,
            file_type="markdown",
            record_type=record_type
        )
        assert metadata.record_type == record_type
    
    # 无效的record_type应该抛出ValidationError
    with pytest.raises(ValidationError):
        ChunkMetadata(
            doc_id="test",
            zone_id="cyber",
            filename="test.md",
            source_path="/path/test.md",
            extension=".md",
            chunk_index=0,
            chunk_count=1,
            char_len=10,
            content_hash="hash",
            mtime=1234567890,
            size_bytes=100,
            file_type="markdown",
            record_type="invalid_type"  # 无效的record_type
        )


def test_metadata_extra_fields_rejection():
    """测试metadata非法字段拒收行为"""
    # 额外字段应该被拒绝
    with pytest.raises(ValidationError):
        ChunkMetadata(
            doc_id="test",
            zone_id="cyber",
            filename="test.md",
            source_path="/path/test.md",
            extension=".md",
            chunk_index=0,
            chunk_count=1,
            char_len=10,
            content_hash="hash",
            mtime=1234567890,
            size_bytes=100,
            file_type="markdown",
            extra_field="value"  # 额外字段
        )


def test_chunk_record_extra_fields_rejection():
    """测试ChunkRecord非法字段拒收行为"""
    metadata = ChunkMetadata(
        doc_id="test",
        zone_id="cyber",
        filename="test.md",
        source_path="/path/test.md",
        extension=".md",
        chunk_index=0,
        chunk_count=1,
        char_len=10,
        content_hash="hash",
        mtime=1234567890,
        size_bytes=100,
        file_type="markdown"
    )
    
    # 额外字段应该被拒绝
    with pytest.raises(ValidationError):
        ChunkRecord(
            text="test",
            vector=[1.0, 2.0, 3.0],
            metadata=metadata,
            extra_field="value"  # 额外字段
        )


def test_chunk_metadata_field_constraints():
    """测试ChunkMetadata字段约束"""
    # chunk_index应该大于等于0
    with pytest.raises(ValidationError):
        ChunkMetadata(
            doc_id="test",
            zone_id="cyber",
            filename="test.md",
            source_path="/path/test.md",
            extension=".md",
            chunk_index=-1,  # 无效值
            chunk_count=1,
            char_len=10,
            content_hash="hash",
            mtime=1234567890,
            size_bytes=100,
            file_type="markdown"
        )
    
    # chunk_count应该大于0
    with pytest.raises(ValidationError):
        ChunkMetadata(
            doc_id="test",
            zone_id="cyber",
            filename="test.md",
            source_path="/path/test.md",
            extension=".md",
            chunk_index=0,
            chunk_count=0,  # 无效值
            char_len=10,
            content_hash="hash",
            mtime=1234567890,
            size_bytes=100,
            file_type="markdown"
        )
    
    # size_bytes应该大于等于0
    with pytest.raises(ValidationError):
        ChunkMetadata(
            doc_id="test",
            zone_id="cyber",
            filename="test.md",
            source_path="/path/test.md",
            extension=".md",
            chunk_index=0,
            chunk_count=1,
            char_len=10,
            content_hash="hash",
            mtime=1234567890,
            size_bytes=-1,  # 无效值
            file_type="markdown"
        )