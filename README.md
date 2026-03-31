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

## 最终利用demo截图：

![image.png](https://chenhun.oss-cn-beijing.aliyuncs.com/photo/202603312006110.png)
