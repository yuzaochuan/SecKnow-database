from __future__ import annotations

from pathlib import Path

from secknow.vector_store.services.sparse import MemoryBm25Index, SQLiteFtsSparseIndex
from secknow.vector_store.services.vector_service import VectorInfrastructureService
from secknow.vector_store.stores.faiss_sqlite_store import FaissSqliteVectorStore
from secknow.vector_store.stores.qdrant_store import QdrantVectorStore


def build_online_service(
    *,
    qdrant_host: str = "localhost",
    qdrant_port: int = 6333,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    distance: str = "cosine",
) -> VectorInfrastructureService:
    """构建在线向量服务（Qdrant + 内存 BM25）。

    能力边界：
    - dense_store: QdrantVectorStore，支持完整的 search/hybrid_search/delete/replace_document/export_zone
    - sparse_index: MemoryBm25Index，数据仅存在于内存，重启后需重新 upsert
    - 适用场景：生产环境实时查询，需要持久化存储和高可用
    - 注意：sparse 索引不持久化，服务重启后需从 dense_store 重新加载数据
    """
    dense_store = QdrantVectorStore(
        host=qdrant_host,
        port=qdrant_port,
        embedding_model=embedding_model,
        distance=distance,
    )
    sparse_index = MemoryBm25Index()
    return VectorInfrastructureService(dense_store=dense_store, sparse_index=sparse_index)


def build_offline_service(
    *,
    db_path: str | Path = "db/secknow.sqlite3",
    index_dir: str | Path = "db/faiss",
    embedding_dim: int = 384,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    distance: str = "cosine",
) -> VectorInfrastructureService:
    """构建离线向量服务（FAISS + SQLite FTS）。

    能力边界：
    - dense_store: FaissSqliteVectorStore，支持完整的 search/hybrid_search/delete/replace_document/export_zone
    - sparse_index: SQLiteFtsSparseIndex，数据持久化在 SQLite FTS5 中
    - 适用场景：离线批处理、本地部署、数据导出/迁移
    - 注意：所有数据（dense/sparse）均持久化，重启后自动恢复
    """
    dense_store = FaissSqliteVectorStore(
        db_path=db_path,
        index_dir=index_dir,
        embedding_dim=embedding_dim,
        embedding_model=embedding_model,
        distance=distance,
    )
    sparse_index = SQLiteFtsSparseIndex(db_path=db_path)
    return VectorInfrastructureService(dense_store=dense_store, sparse_index=sparse_index)


def build_vector_service(
    *,
    mode: str = "online",
    **kwargs: object,
) -> VectorInfrastructureService:
    """统一构建入口。

    参数：
    - mode: "online" 或 "offline"，决定使用哪种存储后端
    - **kwargs: 传递给对应的 build_*_service 函数

    两种模式的能力边界一致：
    - search(): 默认只查询 record_type=knowledge，支持 filters 白名单过滤
    - hybrid_search(): dense 和 sparse 两路遵守相同的 filters
    - delete_by_doc_id(): 按文档 ID 删除所有 chunk，同步清理 sparse 索引
    - replace_document(): 先删除旧文档再插入新记录，保证原子性
    - export_zone(): 返回统一的统计字段（record_count, baseline_count）
    """
    if mode == "online":
        return build_online_service(**kwargs)
    if mode == "offline":
        return build_offline_service(**kwargs)
    raise ValueError("mode must be either 'online' or 'offline'")
