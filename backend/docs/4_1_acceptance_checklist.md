# SecKnow 4.1 文本处理模块 — 验收清单

**适用范围**：本分支（`feat/4.1-phase2`）相对仓库内 4.3 契约与 Phase 1 交接说明的核对表。

**图例**

- **已满足**：实现且与契约/约定一致  
- **部分满足**：有实现但有边界、启发式或可选依赖限制  
- **不在范围**：属其它模块或 Phase 约定不要求

---

## A. 数据契约与产出（对 4.3）


| 编号  | 验收项                                       | 状态  | 说明                                      |
| --- | ----------------------------------------- | --- | --------------------------------------- |
| A1  | 稳定产出 `list[ChunkRecord]`                  | 已满足 | `DocumentTextPipeline` / `run_pipeline` |
| A2  | `text` / `vector` / `metadata` 必填字段齐全     | 已满足 | 与 `vector_store/models.py` 一致           |
| A3  | `zone_id` 仅 `cyber` / `ai` / `crypto`     | 已满足 | 类型字面量 + 调用方传入                           |
| A4  | `record_type` 支持 `knowledge` / `baseline` | 已满足 | 流水线参数                                   |
| A5  | `content_hash` 基于块内容                      | 已满足 | `build_content_hash`                    |
| A6  | `chunk_index` 从 0 连续、`chunk_count` 一致     | 已满足 | 基于**去重后**列表，与 handoff 一致                |
| A7  | `chunk_id` 可空由 4.3 生成                     | 已满足 | 未强制上游填写                                 |


---

## B. 加载（多格式）


| 编号  | 验收项                   | 状态   | 说明                                           |
| --- | --------------------- | ---- | -------------------------------------------- |
| B1  | PDF 文本层抽取             | 已满足  | PyMuPDF `get_text`                           |
| B2  | 扫描/图片型 PDF（OCR）       | 部分满足 | 依赖系统 Tesseract + `pytesseract`；未装则退回嵌入层，可能很短 |
| B3  | PDF 表格结构化             | 部分满足 | `find_tables`→Markdown 表；复杂合并单元格/多栏有限        |
| B4  | DOCX / Markdown / TXT | 已满足  | 既有 loader                                    |
| B5  | 代码类扩展名                | 已满足  | `config.SUPPORTED_EXTS` + `load_code`        |


---

## C. 清洗


| 编号  | 验收项                       | 状态   | 说明                                       |
| --- | ------------------------- | ---- | ---------------------------------------- |
| C1  | 控制字符、换行、BOM、空行            | 已满足  | `basic_clean`                            |
| C2  | 全角 ASCII 区标点、宽空格（正文）      | 已满足  | `normalize_prose`；代码路径不映射 FF 区           |
| C3  | Markdown 专用（如 HTML 注释、空行） | 部分满足 | 轻量规则，非 AST 级                             |
| C4  | 代码专用（行尾空白等）               | 部分满足 | 轻量，无格式化器                                 |
| C5  | PDF 页眉页脚弱化                | 部分满足 | 启发式 + `PDF_PAGE_BOUNDARY`；OCR 后行结构可能削弱效果 |
| C6  | 页眉页脚版面/OCR 级「可靠」          | 部分满足 | 文档已写明局限，非版式引擎                            |


---

## D. 分块 / 去重 / 编码


| 编号  | 验收项                        | 状态   | 说明                                                            |
| --- | -------------------------- | ---- | ------------------------------------------------------------- |
| D1  | 多策略分块（非仅固定窗）               | 已满足  | `hybrid` / `fixed_window` / `paragraph` / `line` / `semantic` |
| D2  | 语义分块（嵌入驱动）                 | 已满足  | LangChain `SemanticChunker`；`EMBEDDING_MODE=fake` 不可用         |
| D3  | 精确去重                       | 已满足  | `exact`                                                       |
| D4  | 近似去重（MinHash）              | 已满足  | `minhash` + datasketch                                        |
| D5  | SBERT 与 fake 向量            | 已满足  | `build_embedder`                                              |
| D6  | LlamaIndex 并行实现语义分块        | 不在范围 | 选用 LangChain 单路径                                              |
| D7  | LangChain 接管全文加载与整条 RAG 管线 | 不在范围 | 仅语义分块用 LangChain                                              |


---

## E. 对外接口与工程化


| 编号  | 验收项                                                                            | 状态   | 说明                              |
| --- | ------------------------------------------------------------------------------ | ---- | ------------------------------- |
| E1  | 门面 `load_document` / `chunk_text` / `dedup` / `encode_chunks` / `run_pipeline` | 已满足  | `facade.py`                     |
| E2  | `load_document(..., normalize=True)` 与流水线清洗一致                                  | 已满足  |                                 |
| E3  | `process_text` 无写盘                                                             | 已满足  |                                 |
| E4  | 批量联调脚本 4.1→4.3                                                                 | 已满足  | `phase1_ingest_data.py`         |
| E5  | 单元测试覆盖主要路径                                                                     | 已满足  | loaders / cleaners / chunkers 等 |
| E6  | REST 上传与 HTTP API                                                              | 不在范围 | 4.5；本仓库无 `api/`                 |
| E7  | 前端联调                                                                           | 不在范围 | handoff Phase 1 可不要求            |


---

## F. 设计方案中的理想接口形态（对照）


| 编号  | 验收项                                 | 状态   | 说明                                  |
| --- | ----------------------------------- | ---- | ----------------------------------- |
| F1  | `chunk_text` / `dedup` 返回富 Chunk 对象 | 部分满足 | 门面仍为 `list[str]`；`ChunkRecord` 在流水线 |
| F2  | 嵌入效果/增量同步「最优」                       | 不在范围 | handoff Phase 1 不要求                 |


---

## 汇总与结论

- **约 28 项**已满足；**约 9 项**部分满足（OCR/表格/清洗深度、PDF 启发式、门面返回类型等）；**约 5 项**不在范围（4.5 API、前端、LlamaIndex 双栈、全文 LC 管线、Phase 1 非目标项）。

**结论**：本分支在「4.1 文本处理子系统 + 面向 4.3 的 `ChunkRecord` 契约 + Phase 1 联调边界」下可判定为**已完成**；与全产品设计方案相比，HTTP 层、双框架全文管线及部分深度清洗/版式仍为**部分满足**或**不在本模块范围**。