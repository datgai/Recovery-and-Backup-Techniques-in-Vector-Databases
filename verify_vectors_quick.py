import numpy as np
from time import sleep

def generate_query_vector(dim=100):
    return np.random.rand(1, dim).astype("float32")[0]

# -------------------
# QDRANT Verification
# -------------------
def verify_qdrant():
    from qdrant_client import QdrantClient

    client = QdrantClient(host="localhost", port=6333)
    query_vector = generate_query_vector(dim=100)
    collection_name = "test_glove" 

    try:
        sleep(1) 
        hits = client.search(
            collection_name="test_glove",
            query_vector=query_vector.tolist(),
            limit=5
            )
        print(f"✅ Qdrant search result count for '{collection_name}':", len(hits))
        if len(hits) > 0:
            print(f"   First Qdrant hit ID: {hits[0].id}, Score: {hits[0].score:.4f}")
    except Exception as e:
        print(f"❌ Qdrant verification failed for '{collection_name}':", e)

# -------------------
# pgvector Verification
# -------------------
def verify_pgvector():
    import psycopg2
    query_vec = generate_query_vector(dim=100) 
    table_name = "items_glove" 

    conn = None
    cur = None
    try:
        conn = psycopg2.connect(
            dbname="vectors", user="postgres", password="password", host="localhost", port=5432
        )
        cur = conn.cursor()
        py_vec = [float(x) for x in query_vec]
        cur.execute(
            f"SELECT id, embedding <-> %s::vector AS distance, word FROM {table_name} ORDER BY distance LIMIT 5;",
            (py_vec,)
        )
        results = cur.fetchall()
        print(f"✅ pgvector search result count for '{table_name}':", len(results))
        if len(results) > 0:
            print(f"   First pgvector hit ID: {results[0][0]}, Distance: {results[0][1]:.4f}, Word: {results[0][2]}")
    except Exception as e:
        print(f"❌ pgvector verification failed for '{table_name}':", e)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

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

    query_vector = generate_query_vector(dim=100)
    collection_name = "VectorDocGlove" 

    try:
        sleep(1)
        collection = client.collections.get(collection_name)
        results = collection.query.near_vector(
            near_vector=query_vector.tolist(),
            limit=5,
            return_properties=["word"] 
        )
        objects = results.objects
        print(f"✅ Weaviate search result count for '{collection_name}':", len(objects))
        if len(objects) > 0:
            print(f"   First Weaviate hit ID: {objects[0].uuid}, Word: {objects[0].properties['word']}")
    except Exception as e:
        print(f"❌ Weaviate verification failed for '{collection_name}':", e)
    finally:
        client.close()

# -------------------
# CHROMA Verification
# -------------------
def verify_chroma():
    import chromadb
    client = chromadb.HttpClient(host="localhost", port=8000)
    collection_name = "test_glove" 

    try:
        sleep(1)
        collection = client.get_collection(name=collection_name)
        query_vector = generate_query_vector(dim=100) # Ensure 100-dim query vector
        result = collection.query(query_embeddings=[query_vector.tolist()], n_results=5)
        
        print(f"✅ Chroma search result count for '{collection_name}':", len(result["ids"][0]))
        if len(result["ids"][0]) > 0:
            print(f"   First Chroma hit ID: {result['ids'][0][0]}, Document: {result['documents'][0][0]}")
    except Exception as e:
        print(f"❌ Chroma verification failed for '{collection_name}':", e)

# -------------------
# MAIN
# -------------------
if __name__ == "__main__":
    print("🔍 Verifying vector presence in each database using 100-dim query vectors...")

    sleep(2) 

    verify_qdrant()
    verify_chroma()
    verify_weaviate()
    verify_pgvector()

    print("\nVerification process completed.")