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
├── __init__.py
├── facade.py                     # 对外统一入口：load_document / chunk_text / dedup / encode_chunks / run_pipeline
├── config.py                     # 4.1 模块配置：分块参数、支持格式、默认编码模型、去重阈值等
├── exceptions.py                 # 文本处理模块专用异常定义
│
├── loaders/                      # 文档加载层：负责“文件 -> 原始文本”
│   ├── __init__.py
│   ├── base.py                   # Loader 抽象接口
│   ├── router.py                 # 按扩展名/文件类型选择对应 loader
│   ├── pdf_loader.py             # PDF 提取
│   ├── docx_loader.py            # DOCX 提取
│   ├── markdown_loader.py        # Markdown 提取
│   ├── text_loader.py            # TXT / 通用纯文本
│   └── code_loader.py            # 代码文件读取
│
├── cleaners/                     # 文本清洗层：负责“原始文本 -> 规范化文本”
│   ├── __init__.py
│   ├── basic.py                  # 基础清洗：空白、换行、控制字符
│   ├── markdown.py               # Markdown 特殊清洗策略（可选保留/去语法）
│   ├── code.py                   # 代码文本清洗策略
│   └── normalize.py              # 通用规范化工具
│
├── chunkers/                     # 分块层：负责“文本 -> chunk 列表”
│   ├── __init__.py
│   ├── base.py                   # Chunker 抽象接口
│   ├── fixed_window.py           # 固定窗口 / overlap 分块
│   ├── paragraph.py              # 按段落分块
│   ├── line.py                   # 按行分块
│   ├── semantic.py               # 语义分块（后续接 LangChain / LlamaIndex）
│   └── router.py                 # 根据 strategy 选择分块器
│
├── dedupers/                     # 去重层：负责“chunk 列表 -> 去重后 chunk 列表”
│   ├── __init__.py
│   ├── exact.py                  # 精确去重（md5/content_hash）
│   ├── minhash.py                # 近似去重（DataSketch / MinHash）
│   └── router.py                 # 按策略切换 exact / minhash
│
├── encoders/                     # 编码层：负责“chunk -> vector”
│   ├── __init__.py
│   ├── base.py                   # Encoder 抽象接口
│   ├── sbert.py                  # SBERT / sentence-transformers 编码器
│   ├── factory.py                # 根据配置加载指定编码模型
│   └── cache.py                  # 可选：编码缓存
│
├── metadata/                     # 元数据构建层
│   ├── __init__.py
│   ├── document.py               # 文档级元数据构建
│   ├── chunk.py                  # chunk 级元数据构建
│   └── hashing.py                # content_hash / doc_id 等计算
│
├── pipeline/                     # 流水线编排层
│   ├── __init__.py
│   ├── load_stage.py             # load_document 阶段
│   ├── chunk_stage.py            # chunk_text 阶段
│   ├── dedup_stage.py            # dedup 阶段
│   ├── encode_stage.py           # encode_chunks 阶段
│   └── run_pipeline.py           # 总编排
│
├── schemas/                      # 4.1 模块内部的数据定义（不是 4.3 的最终 models）
│   ├── __init__.py
│   ├── document.py               # RawDocument / CleanDocument
│   ├── chunk.py                  # RawChunk / TextChunk
│   └── pipeline_result.py        # run_pipeline 中间结果
│
└── tests/
    ├── test_loaders.py
    ├── test_cleaners.py
    ├── test_chunkers.py
    ├── test_dedupers.py
    ├── test_encoders.py
    └── test_pipeline.py
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

## 4.3 测试与验收

### 测试目录结构

```text
backend/tests/vector_store/
├── fixtures.py                 # 统一测试数据
├── test_models.py              # 模型与契约测试
├── test_online_store.py        # 在线存储查询测试
├── test_offline_store.py       # 离线存储查询测试
├── test_hybrid_search.py       # 混合检索专项测试
├── test_export.py              # 导出测试
└── test_document_ops.py        # 文档级操作测试
```

### 运行测试

#### 运行所有测试

```bash
cd backend
pytest tests/vector_store/ -v
```

#### 运行特定测试文件

```bash
# 运行模型与契约测试
pytest tests/vector_store/test_models.py -v

# 运行在线存储测试
pytest tests/vector_store/test_online_store.py -v

# 运行离线存储测试
pytest tests/vector_store/test_offline_store.py -v

# 运行混合检索测试
pytest tests/vector_store/test_hybrid_search.py -v

# 运行导出测试
pytest tests/vector_store/test_export.py -v

# 运行文档级操作测试
pytest tests/vector_store/test_document_ops.py -v
```

### 验收点

#### Online 存储验收点

1. **服务初始化**：Qdrant 连接正常，集合创建成功
2. **数据 upsert**：knowledge 和 baseline 数据成功入库
3. **向量检索**：默认只返回 knowledge 类型的结果
4. **过滤逻辑**：支持按 doc_id、filename、file_type 等字段过滤
5. **基线提取**：get_baseline() 只返回 baseline 类型的结果
6. **删除操作**：删除后查询结果正确更新
7. **导出功能**：导出产物完整，manifest 字段齐全

#### Offline 存储验收点

1. **服务初始化**：FAISS + SQLite 初始化成功
2. **数据 upsert**：knowledge 和 baseline 数据成功入库
3. **向量检索**：默认只返回 knowledge 类型的结果
4. **过滤逻辑**：支持按 doc_id、filename、file_type 等字段过滤
5. **基线提取**：get_baseline() 只返回 baseline 类型的结果
6. **删除操作**：删除后查询结果正确更新
7. **导出功能**：导出产物完整，manifest 字段齐全

### 测试口径

#### 查询语义一致

- **测试目标**：验证 online 和 offline 存储在相同输入下返回语义一致的结果
- **测试方法**：使用相同的测试数据和查询向量，分别测试在线和离线存储
- **验收标准**：两者返回的结果集在 chunk_id、doc_id、score 排序等方面保持一致

#### Hybrid/Search 过滤一致

- **测试目标**：验证 hybrid_search() 与 search() 在过滤规则上保持一致
- **测试方法**：使用相同的过滤条件，分别测试普通搜索和混合搜索
- **验收标准**：两者返回的结果都符合过滤条件，不混入其他文件或文档的内容

### 文档级操作验收

- **删除操作**：按文档 ID 删除所有相关 chunk 后，查询结果中不再包含该文档的内容
- **更新操作**：文档更新后，旧 chunk 不残留，只返回更新后的内容
- **数据隔离**：baseline 和 knowledge 数据不串流，各自独立

### 演示脚本

保留 `backend/scripts/phase1_smoke.py` 作为人工联调用例，用于快速验证核心链路：

```bash
# 在线模式
PYTHONPATH=src python -m scripts.phase1_smoke

# 离线模式
VECTOR_MODE=offline PYTHONPATH=src python -m scripts.phase1_smoke
```

**注意**：smoke 脚本仅用于演示和人工联调，不承担完整回归测试职责。完整回归测试请运行自动化测试套件。
