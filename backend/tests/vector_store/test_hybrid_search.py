from __future__ import annotations

import pytest
import tempfile
from pathlib import Path

from backend.src.secknow.vector_store.services.vector_service import VectorInfrastructureService
from backend.src.secknow.vector_store.stores.faiss_sqlite_store import FaissSqliteVectorStore
from backend.src.secknow.vector_store.services.sparse import SparseTextIndex
from backend.tests.vector_store.fixtures import get_test_records, get_test_filters, get_test_queries


class TestHybridSearch:
    """测试hybrid检索专项功能"""
    
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
    
    def test_hybrid_search_default_returns_only_knowledge(self, vector_service):
        """测试hybrid_search默认不返回baseline"""
        # 搜索cyber分区
        query = "安全指南"
        query_vec = [0.0, 0.0, 0.0]
        results = vector_service.hybrid_search("cyber", query, query_vec, top_k=10)
        
        # 检查所有结果都是knowledge类型
        for hit in results:
            assert hit.metadata.get("record_type") == "knowledge"
    
    def test_hybrid_search_with_filename_filter(self, vector_service):
        """测试filters={"filename": ...}时hybrid不会混入别的文件"""
        query = "安全指南"
        query_vec = [0.0, 0.0, 0.0]
        filters = {"filename": "security_guide.md"}
        
        # 执行hybrid搜索
        results = vector_service.hybrid_search("cyber", query, query_vec, top_k=10, filters=filters)
        
        # 检查所有结果都来自security_guide.md
        for hit in results:
            assert hit.metadata.get("filename") == "security_guide.md"
    
    def test_hybrid_search_with_doc_id_filter(self, vector_service):
        """测试filters={"doc_id": ...}时hybrid不会混入别的文档"""
        query = "安全指南"
        query_vec = [0.0, 0.0, 0.0]
        filters = {"doc_id": "doc1"}
        
        # 执行hybrid搜索
        results = vector_service.hybrid_search("cyber", query, query_vec, top_k=10, filters=filters)
        
        # 检查所有结果都来自doc1
        for hit in results:
            assert hit.doc_id == "doc1"
    
    def test_hybrid_search_filter_consistency_with_search(self, vector_service):
        """验证hybrid_search()与search()在过滤规则上不冲突"""
        query = "安全指南"
        query_vec = [0.0, 0.0, 0.0]
        filters = {"file_type": "markdown"}
        
        # 执行普通搜索
        search_results = vector_service.search("cyber", query_vec, top_k=10, filters=filters)
        
        # 执行hybrid搜索
        hybrid_results = vector_service.hybrid_search("cyber", query, query_vec, top_k=10, filters=filters)
        
        # 检查两种搜索结果的过滤逻辑一致（都只返回markdown类型）
        for hit in search_results:
            assert hit.metadata.get("file_type") == "markdown"
        
        for hit in hybrid_results:
            assert hit.metadata.get("file_type") == "markdown"
    
    def test_hybrid_search_with_invalid_filter_field(self, vector_service):
        """测试hybrid_search对非法字段的处理"""
        query = "安全指南"
        query_vec = [0.0, 0.0, 0.0]
        # 使用非法字段
        filters = {"invalid_field": "value"}
        
        # 执行hybrid搜索（应该忽略非法字段，正常执行）
        results = vector_service.hybrid_search("cyber", query, query_vec, top_k=10, filters=filters)
        
        # 检查结果仍然只返回knowledge类型
        for hit in results:
            assert hit.metadata.get("record_type") == "knowledge"