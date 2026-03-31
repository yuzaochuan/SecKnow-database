from core.embedder import Embedder
from core.vector_store import VectorStore


def main():
    query = input("请输入问题：")

    embedder = Embedder()
    query_vec = embedder.encode([query])[0]

    store = VectorStore()
    results = store.search(query_vec)

    print("\n搜索结果：\n")
    for r in results.points:
        print(f"相似度: {r.score:.4f}")
        print(r.payload["text"])
        print("-" * 30)


if __name__ == "__main__":
    main()
