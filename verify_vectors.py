import numpy as np
from time import sleep

# Reuse the same random vector generator for search queries
def generate_query_vector(dim=128):
    return np.random.rand(1, dim).astype("float32")[0]

# -------------------
# QDRANT Verification
# -------------------
def verify_qdrant():
    from qdrant_client import QdrantClient

    client = QdrantClient(host="localhost", port=6333)
    query_vector = generate_query_vector()
    try:
        # Use the correct argument name for QdrantClient.search
        hits = client.search(
            collection_name="test",
            query_vector=query_vector.tolist(),
            limit=5
        )
        print("✅ Qdrant search result count:", len(hits))
    except Exception as e:
        print("❌ Qdrant verification failed:", e)

# -------------------
# pgvector Verification
# -------------------
def verify_pgvector():
    import psycopg2
    query_vec = generate_query_vector()

    try:
        conn = psycopg2.connect(
            dbname="vectors", user="postgres", password="password", host="localhost", port=5432
        )
        cur = conn.cursor()
        # Convert numpy float32 to plain Python float
        py_vec = [float(x) for x in query_vec]
        cur.execute(
            "SELECT id, embedding <-> %s::vector AS distance FROM items ORDER BY distance LIMIT 5;",
            (py_vec,)
        )
        results = cur.fetchall()
        print("✅ pgvector search result count:", len(results))
        cur.close()
        conn.close()
    except Exception as e:
        print("❌ pgvector verification failed:", e)

# -------------------
# WEAVIATE Verification
# -------------------
def verify_weaviate():
    import weaviate

    client = weaviate.connect_to_local(
        host="localhost",
        port=8080,
        grpc_port=50051
    )

    query_vector = generate_query_vector()

    try:
        # Use the new v4+ query API
        collection = client.collections.get("VectorDoc")
        results = collection.query.near_vector(
            near_vector=query_vector.tolist(),
            limit=5,
            return_properties=["content"]
        )
        objects = results.objects
        print("✅ Weaviate search result count:", len(objects))
    except Exception as e:
        print("❌ Weaviate verification failed:", e)
    finally:
        client.close()

# -------------------
# CHROMA Verification
# -------------------
def verify_chroma():
    import chromadb
    client = chromadb.HttpClient(host="localhost", port=8000)

    try:
        collection = client.get_collection(name="test")
        query_vector = generate_query_vector()
        result = collection.query(query_embeddings=[query_vector.tolist()], n_results=5)
        print("✅ Chroma search result count:", len(result["ids"][0]))
    except Exception as e:
        print("❌ Chroma verification failed:", e)

# -------------------
# MAIN
# -------------------
if __name__ == "__main__":
    print("🔍 Verifying vector presence in each database...")

    verify_qdrant()
    verify_chroma()
    verify_weaviate()
    verify_pgvector()
