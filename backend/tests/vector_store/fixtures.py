from __future__ import annotations

from backend.src.secknow.vector_store.models import ChunkMetadata, ChunkRecord, RecordType, ZoneId


# 统一的测试数据
def get_test_records() -> list[ChunkRecord]:
    """生成固定的测试数据，适用于online/offline测试"""
    # 生成测试向量（简化为3维向量）
    def create_vector(i: int) -> list[float]:
        return [float(i), float(i+1), float(i+2)]
    
    # 文档1：知识块
    doc1_records = [
        ChunkRecord(
            text="这是文档1的第一个知识块",
            vector=create_vector(0),
            metadata=ChunkMetadata(
                doc_id="doc1",
                zone_id="cyber",
                filename="security_guide.md",
                source_path="/path/to/security_guide.md",
                extension=".md",
                chunk_index=0,
                chunk_count=2,
                char_len=20,
                content_hash="hash1",
                mtime=1234567890,
                size_bytes=1024,
                file_type="markdown",
                language="zh",
                record_type="knowledge"
            )
        ),
        ChunkRecord(
            text="这是文档1的第二个知识块",
            vector=create_vector(1),
            metadata=ChunkMetadata(
                doc_id="doc1",
                zone_id="cyber",
                filename="security_guide.md",
                source_path="/path/to/security_guide.md",
                extension=".md",
                chunk_index=1,
                chunk_count=2,
                char_len=20,
                content_hash="hash2",
                mtime=1234567890,
                size_bytes=1024,
                file_type="markdown",
                language="zh",
                record_type="knowledge"
            )
        ),
        ChunkRecord(
            text="这是文档1的安全基线",
            vector=create_vector(2),
            metadata=ChunkMetadata(
                doc_id="doc1",
                zone_id="cyber",
                filename="security_guide.md",
                source_path="/path/to/security_guide.md",
                extension=".md",
                chunk_index=2,
                chunk_count=3,
                char_len=15,
                content_hash="hash3",
                mtime=1234567890,
                size_bytes=1024,
                file_type="markdown",
                language="zh",
                record_type="baseline"
            )
        )
    ]
    
    # 文档2：知识块和基线
    doc2_records = [
        ChunkRecord(
            text="这是文档2的知识块",
            vector=create_vector(3),
            metadata=ChunkMetadata(
                doc_id="doc2",
                zone_id="ai",
                filename="ai_best_practices.py",
                source_path="/path/to/ai_best_practices.py",
                extension=".py",
                chunk_index=0,
                chunk_count=2,
                char_len=18,
                content_hash="hash4",
                mtime=1234567891,
                size_bytes=2048,
                file_type="code",
                language="python",
                record_type="knowledge"
            )
        ),
        ChunkRecord(
            text="这是文档2的安全基线",
            vector=create_vector(4),
            metadata=ChunkMetadata(
                doc_id="doc2",
                zone_id="ai",
                filename="ai_best_practices.py",
                source_path="/path/to/ai_best_practices.py",
                extension=".py",
                chunk_index=1,
                chunk_count=2,
                char_len=15,
                content_hash="hash5",
                mtime=1234567891,
                size_bytes=2048,
                file_type="code",
                language="python",
                record_type="baseline"
            )
        )
    ]
    
    return doc1_records + doc2_records


# 测试查询参数
def get_test_filters() -> dict:
    """生成测试用的过滤参数"""
    return {
        "doc1_filter": {"doc_id": "doc1"},
        "doc2_filter": {"doc_id": "doc2"},
        "markdown_filter": {"file_type": "markdown"},
        "code_filter": {"file_type": "code"},
        "zh_filter": {"language": "zh"},
        "python_filter": {"language": "python"},
        "security_guide_filter": {"filename": "security_guide.md"},
        "ai_best_practices_filter": {"filename": "ai_best_practices.py"}
    }


# 测试查询文本
def get_test_queries() -> list[str]:
    """生成测试用的查询文本"""
    return [
        "安全指南",
        "AI最佳实践",
        "基线安全"
    ]