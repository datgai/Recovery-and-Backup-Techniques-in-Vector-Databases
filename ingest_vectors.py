import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
import chromadb
import weaviate
import psycopg2
import requests
import time

def load_glove_vectors(path="glove.6B.100d.txt", n=1000):
    glove_vectors = []
    words = []
    with open(path, encoding="utf8") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            parts = line.strip().split()
            word = parts[0]
            vector = np.array(parts[1:], dtype=np.float32)
            if len(vector) != 100:
                print(f"Warning: Vector for word '{word}' has dimension {len(vector)}, expected 100. Skipping.")
                continue
            words.append(word)
            glove_vectors.append(vector)
    print(f"Loaded {len(glove_vectors)} GloVe vectors.")
    return np.array(glove_vectors), words

# Qdrant
def qdrant_insert():
    client = QdrantClient(host="localhost", port=6333)
    
    collection_name = "test_glove"

    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)

    glove_vectors, _ = load_glove_vectors(n=1000) # Use 1000 vectors as an example

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=100, distance=Distance.COSINE)
    )

    vectors_list = glove_vectors.tolist()
    ids = list(range(len(vectors_list)))
    
    client.upload_collection(
        collection_name=collection_name,
        vectors=vectors_list,
        ids=ids
    )
    print("✅ Qdrant insertion complete.")

# Chroma
def chroma_insert():
    client = chromadb.HttpClient(host="localhost", port=8000)
    collection_name = "test_glove"
    
    try:
        client.delete_collection(collection_name)
    except Exception as e:
        print(f"Could not delete Chroma collection (might not exist): {e}")

    collection = client.get_or_create_collection(name=collection_name)
    
    # Load GloVe vectors
    glove_vectors, words = load_glove_vectors(n=1000)
    
    ids = [str(i) for i in range(len(glove_vectors))]
    embeddings = [vec.tolist() for vec in glove_vectors]
    documents = [f"word_{word}" for word in words] 

    collection.add(ids=ids, embeddings=embeddings, documents=documents)
    print("✅ Chroma insertion complete.")


# Weaviate
def weaviate_insert():
    from weaviate.collections.classes.config import DataType
    from weaviate.collections.classes.config import Configure

    client = None
    try:
        client = weaviate.connect_to_local(host="localhost", port=8080, grpc_port=50051)
    except Exception as e:
        print(f"❌ Could not connect to Weaviate: {e}")
        return

    collection_name = "VectorDocGlove"

    if client.collections.exists(collection_name):
        client.collections.delete(collection_name)
        print(f"Deleted existing Weaviate collection: {collection_name}")

    client.collections.create(
        name=collection_name,
        properties=[{"name": "word", "data_type": DataType.TEXT}],
        vector_index_config=Configure.VectorIndex.hnsw()
    )
    print(f"Created Weaviate collection: {collection_name}")

    glove_vectors, words = load_glove_vectors(n=1000) 
    
    collection = client.collections.get(collection_name)


    with collection.batch.dynamic() as batch:
        for i, vec in enumerate(glove_vectors):
            batch.add_object(
                properties={"word": words[i]},
                vector=vec.tolist() 
            )

    failed_objects = collection.batch.failed_objects
    if failed_objects:
        print(f"Number of failed Weaviate imports: {len(failed_objects)}")
        print(f"First failed Weaviate object: {failed_objects[0]}")
    else:
        print("✅ Weaviate insertion complete.")
    
    client.close() 

# pgvector
def pgvector_insert():
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(
            dbname="vectors", user="postgres", password="password", host="localhost", port=5432
        )
        cur = conn.cursor()

        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("DROP TABLE IF EXISTS items_glove;")
        cur.execute("CREATE TABLE items_glove (id serial PRIMARY KEY, embedding vector(100), word TEXT);")

        glove_vectors, words = load_glove_vectors(n=1000)

        for i, vec in enumerate(glove_vectors):
            cur.execute("INSERT INTO items_glove (embedding, word) VALUES (%s, %s)", (vec.tolist(), words[i]))

        conn.commit()
        print("✅ pgvector table populated with GloVe data.")
    except Exception as e:
        print(f"❌ pgvector insertion failed: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting vector insertion process with GloVe dataset...")

    try:
        with open("glove.6B.100d.txt", 'r') as f:
            pass
    except FileNotFoundError:
        print("Error: glove.6B.100d.txt not found.")
        print("Please download it from https://nlp.stanford.edu/projects/glove/ and place it in the same directory.")
        exit()

    qdrant_insert()
    chroma_insert()
    weaviate_insert()
    pgvector_insert()
    print("✅ All vector insertions attempted successfully.")