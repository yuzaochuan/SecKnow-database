# 给 4.1 同事的接口对接说明

本文档用于 4.1 文本处理模块与 4.3 向量存储模块的 Phase 1 联调。

## 1. 联调目标

Phase 1 不追求最终检索效果，优先保证以下事项稳定：

- 4.1 能稳定产出 `list[ChunkRecord]`
- 4.3 能按契约完成 upsert
- 普通知识检索与安全基线读取能够按预期分流

## 2. 唯一契约来源

联调时请以 [models.py](/Users/zaochuan/Documents/code/python/SecKnow/backend/src/secknow/vector_store/models.py) 为准。

最重要的三个结构是：

- `ChunkMetadata`
- `ChunkRecord`
- `generate_chunk_id()`

## 3. 4.1 需要提供什么

4.1 最终交给 4.3 的数据结构是：

```python
list[ChunkRecord]
```

单条 `ChunkRecord` 至少需要包含：

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

可选字段：

- `metadata.language`
- `metadata.chunk_id`

## 4. 最关键的字段说明

### `zone_id`

作用：

- 表示该记录属于哪个知识分区

当前只允许：

- `cyber`
- `ai`
- `crypto`

注意：

- `upsert(zone_id=...)` 的参数必须和 `metadata.zone_id` 保持一致

### `record_type`

作用：

- 用于区分“普通知识块”和“安全基线块”

可选值：

- `knowledge`
- `baseline`

默认值：

- `knowledge`

约定：

- 普通知识检索数据请使用 `knowledge`
- 如果该记录是给 4.2 安全审查模块使用的基线，请显式设为 `baseline`

### `content_hash`

作用：

- 用于稳定生成 `chunk_id`
- 用于幂等 upsert
- 用于增量更新判断

建议：

- 以 chunk 原文内容为输入计算哈希
- 同一块内容未变时，尽量保持 `content_hash` 不变

### `chunk_index`

作用：

- 表示当前 chunk 在原文档中的顺序

要求：

- 从 `0` 开始
- 同一文档内应连续且稳定

### `chunk_count`

作用：

- 表示该文档最终总共被切成多少块

要求：

- 必须大于 `0`
- 同一文档内每条记录的 `chunk_count` 应一致

## 5. `chunk_id` 是怎么来的

如果 4.1 不主动提供 `chunk_id`，4.3 会自动生成：

```python
sha1(f"{doc_id}:{chunk_index}:{content_hash}")
```

这意味着：

- 同一个文档块重复处理时，只要 `doc_id + chunk_index + content_hash` 不变，`chunk_id` 就保持稳定
- 4.3 可以安全执行幂等 upsert，而不是产生重复记录

## 6. 当前默认行为

### 普通检索

- `search()` 默认只查 `record_type=knowledge`
- `hybrid_search()` 默认也只返回 `knowledge`

### 安全基线

- `baseline` 不参与默认普通检索
- 4.2 安全审查模块通过 `get_baseline(zone_id)` 读取基线向量

因此请不要把“给 4.2 的基线数据”和“给问答检索的知识数据”混用。

## 7. 最小构造示例

```python
from secknow.vector_store.models import ChunkMetadata, ChunkRecord

record = ChunkRecord(
    text="发生主机入侵事件后，优先隔离主机并保留日志。",
    vector=[0.1, 0.2, 0.3],
    metadata=ChunkMetadata(
        doc_id="doc-001",
        zone_id="cyber",
        filename="incident.md",
        source_path="/data/incident.md",
        extension=".md",
        chunk_index=0,
        chunk_count=1,
        char_len=24,
        content_hash="your-content-hash",
        mtime=1712000000,
        size_bytes=128,
        file_type="markdown",
        language="zh",
        record_type="knowledge",
    ),
)
```

## 8. 推荐联调顺序

1. 4.1 先构造 1 到 3 条最小 `ChunkRecord`
2. 先全部使用 `record_type="knowledge"` 跑通入库
3. 再补 1 到 2 条 `record_type="baseline"` 验证 4.2 基线读取
4. 确认字段稳定后，再扩大到真实批量数据

## 9. 本地验证方式

在 4.3 模块目录下运行：

```bash
PYTHONPATH=src python -m scripts.phase1_smoke
```

如果需要在线模式，请先启动本地 Docker Qdrant：

```bash
docker run -d --name secknow-qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

smoke 脚本会验证：

- upsert
- search
- hybrid_search
- get_baseline

## 10. Phase 1 暂不要求 4.1 处理的事

- 不要求最终 embedding 模型效果最优
- 不要求复杂增量同步策略
- 不要求 API 层接入
- 不要求前端联调

当前最重要的是：字段契约稳定、最小链路跑通。
