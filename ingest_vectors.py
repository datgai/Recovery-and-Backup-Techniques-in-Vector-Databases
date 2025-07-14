import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
import chromadb
import weaviate
import psycopg2
import requests
import time

def random_vectors(n=1000, dim=128):
    return np.random.rand(n, dim).astype("float32")

# Qdrant
def qdrant_insert():
    client = QdrantClient(host="localhost", port=6333)
    
    collection_name = "test"

    # Check and delete the collection if it exists
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)

    # Create a new collection
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=128, distance=Distance.COSINE)
    )

    vectors = random_vectors().tolist()

    # Insert vectors with IDs
    client.upload_collection(
        collection_name=collection_name,
        vectors=vectors,
        ids=list(range(len(vectors)))
    )

# Chroma
def chroma_insert():
    client = chromadb.HttpClient(host="localhost", port=8000)
    collection = client.get_or_create_collection(name="test")
    vectors = random_vectors()
    ids = [str(i) for i in range(len(vectors))]
    embeddings = [vec.tolist() for vec in vectors]
    documents = [f"doc_{i}" for i in range(len(vectors))]
    collection.add(ids=ids, embeddings=embeddings, documents=documents)

# Weaviate
def weaviate_insert():
    import weaviate
    from weaviate.collections.classes.config import DataType
    from weaviate.classes.config import Configure

    try:
        client = weaviate.connect_to_local(host="localhost", port=8080, grpc_port=50051)
    except Exception as e:
        print(f"❌ Could not connect to Weaviate: {e}")
        return

    # Remove class if exists
    if client.collections.exists("VectorDoc"):
        client.collections.delete("VectorDoc")

    # Create class/collection with HNSW vector index
    client.collections.create(
        name="VectorDoc",
        properties=[{"name": "content", "data_type": DataType.TEXT}],
        vector_index_config=Configure.VectorIndex.hnsw()
    )

    # Insert data
    for i, vec in enumerate(random_vectors()):
        client.collections.get("VectorDoc").data.insert(
            properties={"content": f"doc_{i}"},
            vector=vec.tolist()
        )
    client.close()


#pgvector
def pgvector_insert():
    conn = psycopg2.connect(
        dbname="vectors", user="postgres", password="password", host="localhost", port=5432
    )
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("DROP TABLE IF EXISTS items;")
    cur.execute("CREATE TABLE items (id serial PRIMARY KEY, embedding vector(128));")

    vectors = np.random.rand(1000, 128).astype(np.float32)
    for vec in vectors:
        cur.execute("INSERT INTO items (embedding) VALUES (%s)", (vec.tolist(),))

    conn.commit()
    cur.close()
    conn.close()
    print("✅ pgvector table populated.")

if __name__ == "__main__":
    qdrant_insert()
    weaviate_insert()
    chroma_insert()
    pgvector_insert()
    print("✅ All vectors inserted successfully.")