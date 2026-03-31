# SecKnow-database

# 前置步骤：

## 需要docker容器

```
docker run -p 6333:6333 qdrant/qdrant
```

## 使用python-venv虚拟环境隔离

```
python3 -m venv SecKnow
```

我在pyrightconfig.json文件里写了我自己的venv路径，你如果要启用，让AI帮你改成你的venv路径或者删掉那一部分
环境依赖：
在这个项目启用虚拟环境后，需要下载两个库

```
pip install sentence-transformers qdrant-client
```

## 目录结构说明：

### 目录

SecKnow/
├── data/ # 数据（你已经有了）
│ └── docs.txt

├── models/ # 模型（可选缓存）
│ └── (自动下载的模型)

├── db/ # 向量数据库持久化（暂未设立）
│ └── qdrant_data/

├── core/ # 🔥核心逻辑（重点）
│ ├── embedder.py
│ └── vector_store.py

├── scripts/ # 脚本（入口）
│ ├── ingest.py
│ └── query.py

├── venv/ # 虚拟环境（你已经有了）
├── pyrightconfig.json
└── README.md

### 核心模块说明

1. embedder.py（语义编码）
   负责将文本转换为向量表示：
   使用 Sentence-BERT 模型
   输入文本 → 输出高维向量
   支持批量编码
   作用：让“文本具备语义可计算能力”
2. vector_store.py（向量数据库封装）
   封装 Qdrant 操作：
   创建集合（Collection）
   插入向量（upsert）
   向量检索（query_points）
   特点：
   使用余弦相似度（Cosine Similarity）
   支持 payload 存储原文
3. ingest.py（文档入库）
   功能：
   读取文本文件
   分行切分（模拟 chunk）
   批量向量化
   写入向量数据库
   执行：
   python -m scripts.ingest
4. query.py（语义查询）
   功能：
   接收用户输入
   转换为向量
   在向量数据库中检索 Top-K
   返回最相关文本

## 最终利用demo截图：

![image.png](https://chenhun.oss-cn-beijing.aliyuncs.com/photo/202603312006110.png)
