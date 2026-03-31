from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


class VectorStore:
    def __init__(self):
        self.client = QdrantClient("localhost", port=6333)
        self.collection_name = "secknow"

    def create_collection(self, dim):
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

    def insert(self, vectors, texts):
        points = []
        for i, (vec, text) in enumerate(zip(vectors, texts)):
            points.append(
                PointStruct(id=i, vector=vec.tolist(), payload={"text": text})
            )
        self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, query_vector, top_k=3):
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector.tolist(),
            limit=top_k,
            with_payload=True,
        )
        return results
