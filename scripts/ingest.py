from core.embedder import Embedder
from core.vector_store import VectorStore


def load_docs():
    with open("data/docs.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines


def main():
    docs = load_docs()

    embedder = Embedder()
    vectors = embedder.encode(docs)

    store = VectorStore()
    store.create_collection(len(vectors[0]))
    store.insert(vectors, docs)

    print("入库完成！")


if __name__ == "__main__":
    main()
