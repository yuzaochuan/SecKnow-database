from __future__ import annotations

import pytest
import tempfile
from pathlib import Path

from backend.src.secknow.vector_store.services.vector_service import VectorInfrastructureService
from backend.src.secknow.vector_store.stores.faiss_sqlite_store import FaissSqliteVectorStore
from backend.src.secknow.vector_store.services.sparse import SparseTextIndex
from backend.tests.vector_store.fixtures import get_test_records


class TestDocumentOps:
    """测试文档级操作功能"""
    
    @pytest.fixture
    def vector_service(self):
        """创建临时的向量服务实例"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            index_dir = Path(tmpdir) / "index"
            
            # 创建存储实例
            dense_store = FaissSqliteVectorStore(
                db_path=str(db_path),
                index_dir=str(index_dir),
                embedding_dim=3,  # 使用简化的3维向量
                embedding_model="test-model"
            )
            
            # 创建稀疏索引
            sparse_index = SparseTextIndex(db_path=str(db_path))
            
            # 创建服务实例
            service = VectorInfrastructureService(
                dense_store=dense_store,
                sparse_index=sparse_index
            )
            
            # 插入测试数据
            test_records = get_test_records()
            for record in test_records:
                # 确保zone存在
                service.ensure_zone(record.metadata.zone_id, 3)
                # 插入数据
                service.upsert(record.metadata.zone_id, [record])
            
            yield service
    
    def test_delete_by_doc_id_equivalent(self, vector_service):
        """测试基于delete方法的文档级删除功能"""
        # 先搜索doc1的所有chunk
        query_vec = [0.0, 0.0, 0.0]
        filters = {"doc_id": "doc1"}
        results_before = vector_service.search("cyber", query_vec, top_k=10, filters=filters)
        assert len(results_before) > 0
        
        # 获取doc1的所有chunk_id
        doc1_chunk_ids = [hit.chunk_id for hit in results_before]
        
        # 删除这些chunk
        vector_service.delete("cyber", doc1_chunk_ids)
        
        # 再次搜索，确认doc1的chunk已被删除
        results_after = vector_service.search("cyber", query_vec, top_k=10, filters=filters)
        assert len(results_after) == 0
    
    def test_document_update_no_old_chunks(self, vector_service):
        """验证文档更新后旧chunk不残留"""
        # 先搜索doc1的所有chunk
        query_vec = [0.0, 0.0, 0.0]
        filters = {"doc_id": "doc1"}
        results_before = vector_service.search("cyber", query_vec, top_k=10, filters=filters)
        old_chunk_ids = [hit.chunk_id for hit in results_before]
        
        # 准备更新后的文档数据（使用不同的content_hash）
        from backend.src.secknow.vector_store.models import ChunkMetadata, ChunkRecord
        updated_records = [
            ChunkRecord(
                text="这是文档1的更新后的知识块",
                vector=[10.0, 11.0, 12.0],
                metadata=ChunkMetadata(
                    doc_id="doc1",
                    zone_id="cyber",
                    filename="security_guide.md",
                    source_path="/path/to/security_guide.md",
                    extension=".md",
                    chunk_index=0,
                    chunk_count=1,
                    char_len=25,
                    content_hash="updated_hash1",  # 不同的content_hash
                    mtime=1234567890,
                    size_bytes=1024,
                    file_type="markdown",
                    language="zh",
                    record_type="knowledge"
                )
            )
        ]
        
        # 插入更新后的数据（upsert）
        vector_service.upsert("cyber", updated_records)
        
        # 搜索doc1的所有chunk
        results_after = vector_service.search("cyber", query_vec, top_k=10, filters=filters)
        
        # 检查结果中没有旧的chunk_id
        new_chunk_ids = [hit.chunk_id for hit in results_after]
        for old_id in old_chunk_ids:
            assert old_id not in new_chunk_ids
        
        # 检查有新的chunk
        assert len(results_after) > 0
    
    def test_baseline_knowledge_no_mix(self, vector_service):
        """验证baseline / knowledge不串数据"""
        # 搜索knowledge类型
        query_vec = [0.0, 0.0, 0.0]
        knowledge_results = vector_service.search("cyber", query_vec, top_k=10)
        
        # 检查所有结果都是knowledge类型
        for hit in knowledge_results:
            assert hit.metadata.get("record_type") == "knowledge"
        
        # 获取baseline
        baseline = vector_service.get_baseline("cyber")
        
        # 检查所有结果都是baseline类型
        for meta in baseline.metadatas:
            assert meta.get("record_type") == "baseline"
        
        # 检查knowledge和baseline的数量符合预期
        assert len(knowledge_results) >= 2  # doc1有2个knowledge
        assert len(baseline.metadatas) >= 1  # doc1有1个baseline