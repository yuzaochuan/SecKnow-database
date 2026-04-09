from __future__ import annotations

import pytest
import tempfile
import json
from pathlib import Path

from backend.src.secknow.vector_store.services.vector_service import VectorInfrastructureService
from backend.src.secknow.vector_store.stores.faiss_sqlite_store import FaissSqliteVectorStore
from backend.src.secknow.vector_store.services.sparse import SparseTextIndex
from backend.tests.vector_store.fixtures import get_test_records


class TestExport:
    """测试导出功能"""
    
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
    
    def test_export_zone_products_exist(self, vector_service):
        """验证export产物存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 导出cyber分区
            result = vector_service.export_zone("cyber", tmpdir)
            
            # 检查导出结果包含必要的文件路径
            assert "zone_id" in result
            assert "target_dir" in result
            assert "sqlite_file" in result
            assert "faiss_file" in result
            assert "manifest_file" in result
            assert "checksums_file" in result
            
            # 检查文件是否存在
            target_dir = Path(result["target_dir"])
            assert target_dir.exists()
            assert Path(result["sqlite_file"]).exists()
            assert Path(result["faiss_file"]).exists()
            assert Path(result["manifest_file"]).exists()
            assert Path(result["checksums_file"]).exists()
    
    def test_export_manifest_fields_complete(self, vector_service):
        """验证manifest字段完整"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 导出cyber分区
            result = vector_service.export_zone("cyber", tmpdir)
            
            # 读取manifest文件
            manifest_path = Path(result["manifest_file"])
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            
            # 检查必要字段是否存在
            required_fields = [
                "zone_id", "engine", "embedding_model", "embedding_dim",
                "distance", "normalized", "chunk_strategy", "build_time",
                "record_count", "baseline_count", "schema_version"
            ]
            for field in required_fields:
                assert field in manifest
            
            # 检查字段值的类型
            assert isinstance(manifest["zone_id"], str)
            assert isinstance(manifest["engine"], str)
            assert isinstance(manifest["embedding_model"], str)
            assert isinstance(manifest["embedding_dim"], int)
            assert isinstance(manifest["distance"], str)
            assert isinstance(manifest["normalized"], bool)
            assert isinstance(manifest["chunk_strategy"], dict)
            assert isinstance(manifest["build_time"], str)
            assert isinstance(manifest["record_count"], int)
            assert isinstance(manifest["baseline_count"], int)
            assert isinstance(manifest["schema_version"], int)
    
    def test_export_record_counts_correct(self, vector_service):
        """验证record_count / baseline_count符合统一定义"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 导出cyber分区
            result = vector_service.export_zone("cyber", tmpdir)
            
            # 读取manifest文件
            manifest_path = Path(result["manifest_file"])
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            
            # 检查record_count和baseline_count
            # 从测试数据中，cyber分区应该有2个knowledge和1个baseline
            assert manifest["record_count"] == 2  # knowledge数量
            assert manifest["baseline_count"] == 1  # baseline数量
    
    def test_export_checksum_exists(self, vector_service):
        """验证checksum或基础完整性"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 导出cyber分区
            result = vector_service.export_zone("cyber", tmpdir)
            
            # 读取checksums文件
            checksums_path = Path(result["checksums_file"])
            assert checksums_path.exists()
            
            with open(checksums_path, "r", encoding="utf-8") as f:
                checksums = json.load(f)
            
            # 检查checksums包含必要的文件
            expected_files = [
                "chunks.sqlite", "faiss.index", 
                "baseline_vectors.npy", "baseline_meta.json", "manifest.json"
            ]
            for file_name in expected_files:
                assert file_name in checksums
                assert isinstance(checksums[file_name], str)
                assert len(checksums[file_name]) == 64  # SHA256 hash长度