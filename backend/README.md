# SecKnow Backend Phase 1（4.3 向量存储模块）

本 README 面向两类同事：

- 4.3 模块开发者：需要了解当前 Phase 1 的边界、运行方式和存储契约
- 4.1 模块开发者：需要明确应该在哪里开发，以及最终如何与 `models.py` 对接

当前第一阶段的目标很明确：

- 先把 4.3 的数据契约和基础链路固定下来
- 让 4.1 能按统一模型产出 `list[ChunkRecord]`
- 让 4.2 / 4.4 / 4.5 后续可以直接复用 4.3 的统一接口

## 整体仓库结构

结合当前项目规划，仓库整体结构如下：

```text
SecKnow/
├── frontend/                    # 4.6 Vue 3 + Vite 前端
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── views/
│   │   └── store/
│   └── package.json
├── backend/                     # Python 后端
│   ├── src/secknow/
│   │   ├── text_processing/     # 4.1 文本处理模块
│   │   ├── safety/              # 4.2 安全审查模块
│   │   ├── vector_store/        # 4.3 向量存储模块
│   │   ├── inference/           # 4.4 推理模块
│   │   ├── api/                 # 4.5 FastAPI 接口层
│   │   ├── ui_report/           # 结果报告/前端联动辅助模块
│   │   ├── alert_board/         # 4.7 告警板模块
│   │   └── shared/              # 公共常量、日志、工具
│   ├── tests/
│   ├── scripts/
│   ├── requirements.txt
│   └── pyrightconfig.json
├── docker-compose.yml
└── README.md
```

### 当前模块分工

- `backend/src/secknow/text_processing/`
  - 4.1 的主要开发位置
  - 负责切分文本、抽取元数据、生成向量前的数据结构
- `backend/src/secknow/safety/`
  - 4.2 的主要开发位置
  - 负责读取 4.3 提供的基线向量，做安全审查比对
- `backend/src/secknow/vector_store/`
  - 4.3 的主要开发位置
  - 负责存储、检索、导出，以及对外统一接口
- `backend/src/secknow/inference/`
  - 4.4 的主要开发位置
  - 负责检索增强与推理调用
- `backend/src/secknow/api/`
  - 4.5 的主要开发位置
  - 负责把 HTTP 请求映射到 4.3 / 4.4 的服务接口

## 4.3 当前目录结构

当前 Phase 1 已落地的 4.3 模块代码位于：

```text
backend/
├── src/secknow/vector_store/
│   ├── models.py                # 统一数据契约
│   ├── config.py                # 分区与通用配置
│   ├── factory.py               # 在线/离线服务装配
│   ├── stores/
│   │   ├── base.py              # 抽象存储接口
│   │   ├── qdrant_store.py      # 在线后端（Qdrant）
│   │   └── faiss_sqlite_store.py# 离线后端（FAISS + SQLite）
│   ├── services/
│   │   ├── sparse.py            # 稀疏检索
│   │   ├── hybrid.py            # dense + sparse 融合
│   │   └── vector_service.py    # 统一服务门面
│   └── schemas/sqlite_schema.sql
├── scripts/phase1_smoke.py      # 本地最小冒烟脚本
└── docs/
    ├── phase1_design.md
    └── for_module_4_1_handoff.md
```

## 4.3 对外契约

Phase 1 的唯一契约来源是：

- `backend/src/secknow/vector_store/models.py`

可以把这个文件理解成“跨模块协议”：

- 4.1 负责构造 `ChunkRecord`
- 4.3 负责存储、检索、导出
- 4.5 后续把请求映射到这些模型
- 4.2 通过 `BaselineBundle` 获取基线向量

最重要的几个模型是：

- `ChunkMetadata`
- `ChunkRecord`
- `SearchHit`
- `BaselineBundle`
- `generate_chunk_id()`

## 给 4.1 同事的对接入口

4.1 模块当前应该在下面这个目录开发：

```text
backend/src/secknow/text_processing/
```

4.1 在 Phase 1 不需要关心 Qdrant、FAISS、SQLite 的实现细节，只需要稳定产出：

```python
list[ChunkRecord]
```

每条 `ChunkRecord` 至少应包含：

- `text`
- `vector`
- `metadata.doc_id`
- `metadata.zone_id`
- `metadata.filename`
- `metadata.source_path`
- `metadata.extension`
- `metadata.chunk_index`
- `metadata.chunk_count`
- `metadata.char_len`
- `metadata.content_hash`
- `metadata.mtime`
- `metadata.size_bytes`
- `metadata.file_type`
- `metadata.language`（可选）

### 4.1 需要特别注意的字段

- `metadata.zone_id`
  - 当前只允许：`cyber` / `ai` / `crypto`
- `metadata.record_type`
  - 默认是 `knowledge`
  - 如果该记录用于 4.2 安全基线，请显式设置为 `baseline`
- `metadata.content_hash`
  - 用于生成稳定 `chunk_id`
  - 会直接影响幂等 upsert
- `metadata.chunk_index`
  - 从 `0` 开始，表示该 chunk 在原文中的顺序
- `metadata.chunk_count`
  - 必须大于 `0`
  - 同一文档内应保持一致

### `chunk_id` 规则

如果 4.1 不传 `chunk_id`，4.3 会自动生成：

```python
sha1(f"{doc_id}:{chunk_index}:{content_hash}")
```

这意味着：

- 同一块内容重跑时，ID 可以保持稳定
- 4.3 可以安全执行幂等 upsert，而不是重复插入

更多细节请直接看：

- `backend/docs/for_module_4_1_handoff.md`

## 当前默认行为

- 普通 `search()` 默认只查 `record_type=knowledge`
- `hybrid_search()` 默认也只返回 `knowledge`
- `record_type=baseline` 的记录不会出现在普通检索结果中
- 4.2 通过 `get_baseline(zone_id)` 单独读取 `baseline`
- 当前 smoke 使用的是“确定性伪向量”，目的是验证链路，不代表真实语义效果

## 本地运行

推荐 Python 版本：

- Python 3.11

推荐先准备虚拟环境，再安装依赖：

```bash
uv venv .venv --python 3.11 --seed
source .venv/bin/activate
uv pip install -r requirements.txt
```

如果你已经激活环境，也可以继续使用：

```bash
pip install -r requirements.txt
```

## 运行 Phase 1 smoke

### 在线模式（默认，连接本地 Docker Qdrant）

启动 Qdrant：

```bash
docker run -d --name secknow-qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

运行：

```bash
PYTHONPATH=src python -m scripts.phase1_smoke
```

可选环境变量：

```bash
QDRANT_HOST=127.0.0.1 QDRANT_PORT=6333 PYTHONPATH=src python -m scripts.phase1_smoke
```

### 离线模式（FAISS + SQLite）

```bash
VECTOR_MODE=offline PYTHONPATH=src python -m scripts.phase1_smoke
```

### smoke 会验证的链路

- `knowledge` upsert
- `baseline` upsert
- 普通 dense search
- `hybrid_search()`
- `get_baseline()`

## Phase 1 边界

已完成：

- 统一数据模型：`ChunkRecord / SearchHit / BaselineBundle / ExportManifest`
- 统一服务契约：`ensure_zone / upsert / search / hybrid_search / delete / export_zone / get_baseline`
- 在线后端：`QdrantVectorStore`
- 离线后端：`FaissSqliteVectorStore`
- dense + sparse 融合：`HybridRetriever`

暂不做：

- IVF-PQ 参数优化
- 完整 REST API
- 前端联调
- 真实召回质量调优

## 推荐联调顺序

1. 4.1 先在 `backend/src/secknow/text_processing/` 内完成最小 chunk 产出
2. 按 `models.py` 构造 1 到 3 条 `ChunkRecord`
3. 先全部用 `record_type="knowledge"` 跑通入库
4. 再补 `record_type="baseline"` 验证 4.2 基线路径
5. 4.3 与 4.1 字段契约稳定后，再进入 Phase 2 优化
