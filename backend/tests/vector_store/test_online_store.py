from __future__ import annotations

import pytest
import tempfile
from pathlib import Path

from backend.src.secknow.vector_store.services.vector_service import VectorInfrastructureService
from backend.src.secknow.vector_store.stores.faiss_sqlite_store import FaissSqliteVectorStore
from backend.src.secknow.vector_store.services.sparse import SparseTextIndex
from backend.tests.vector_store.fixtures import get_test_records, get_test_filters, get_test_queries


class TestOnlineStore:
    """测试在线存储的查询功能"""
    
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
    
    def test_search_default_returns_only_knowledge(self, vector_service):
        """测试无过滤时默认只返回knowledge"""
        # 搜索cyber分区
        query_vec = [0.0, 0.0, 0.0]
        results = vector_service.search("cyber", query_vec, top_k=10)
        
        # 检查所有结果都是knowledge类型
        for hit in results:
            assert hit.metadata.get("record_type") == "knowledge"
    
    def test_search_with_doc_id_filter(self, vector_service):
        """测试doc_id过滤逻辑"""
        query_vec = [0.0, 0.0, 0.0]
        filters = {"doc_id": "doc1"}
        
        # 搜索cyber分区
        results = vector_service.search("cyber", query_vec, top_k=10, filters=filters)
        
        # 检查所有结果都来自doc1
        for hit in results:
            assert hit.doc_id == "doc1"
    
    def test_search_with_filename_filter(self, vector_service):
        """测试filename过滤逻辑"""
        query_vec = [0.0, 0.0, 0.0]
        filters = {"filename": "security_guide.md"}
        
        # 搜索cyber分区
        results = vector_service.search("cyber", query_vec, top_k=10, filters=filters)
        
        # 检查所有结果都来自security_guide.md
        for hit in results:
            assert hit.metadata.get("filename") == "security_guide.md"
    
    def test_search_with_file_type_filter(self, vector_service):
        """测试file_type过滤逻辑"""
        query_vec = [0.0, 0.0, 0.0]
        filters = {"file_type": "markdown"}
        
        # 搜索cyber分区
        results = vector_service.search("cyber", query_vec, top_k=10, filters=filters)
        
        # 检查所有结果都是markdown类型
        for hit in results:
            assert hit.metadata.get("file_type") == "markdown"
    
    def test_get_baseline_returns_only_baseline(self, vector_service):
        """测试get_baseline()只返回baseline"""
        # 获取cyber分区的基线
        baseline = vector_service.get_baseline("cyber")
        
        # 检查所有结果都是baseline类型
        for meta in baseline.metadatas:
            assert meta.get("record_type") == "baseline"
    
    def test_delete_affects_search_results(self, vector_service):
        """测试删除后查询结果变化正确"""
        # 先搜索，获取一个chunk_id
        query_vec = [0.0, 0.0, 0.0]
        results_before = vector_service.search("cyber", query_vec, top_k=10)
        assert len(results_before) > 0
        
        # 删除第一个结果
        chunk_id_to_delete = results_before[0].chunk_id
        vector_service.delete("cyber", [chunk_id_to_delete])
        
        # 再次搜索，确认结果减少
        results_after = vector_service.search("cyber", query_vec, top_k=10)
        
        # 检查被删除的chunk_id不在结果中
        chunk_ids_after = [hit.chunk_id for hit in results_after]
        assert chunk_id_to_delete not in chunk_ids_after
        
        # 检查结果数量减少
        assert len(results_after) < len(results_before)