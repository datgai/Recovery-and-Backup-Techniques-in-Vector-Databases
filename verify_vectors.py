import numpy as np
from qdrant_client import QdrantClient
import chromadb
import weaviate
import psycopg2

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
                continue
            words.append(word)
            glove_vectors.append(vector)
    return np.array(glove_vectors), words

glove_vectors, glove_words = load_glove_vectors(n=1000)

# -------------------
# QDRANT Verification
# -------------------
def verify_qdrant():
    client = QdrantClient(host="localhost", port=6333)
    collection_name = "test_glove"

    correct = 0
    for i, vec in enumerate(glove_vectors):
        hits = client.query_points(
            collection_name=collection_name,
            query=vec.tolist(),
            limit=1
        )
        if hits.points and hits.points[0].id == i:
            correct += 1

    print(f"✅ Qdrant accuracy: {correct}/{len(glove_vectors)} = {correct/len(glove_vectors)*100:.2f}%")

# -------------------
# Chroma Verification
# -------------------
def verify_chroma():
    client = chromadb.HttpClient(host="localhost", port=8000)
    collection = client.get_collection(name="test_glove")

    correct = 0
    for i, vec in enumerate(glove_vectors):
        results = collection.query(query_embeddings=[vec.tolist()], n_results=1)
        result_id = results["ids"][0][0]
        if result_id == str(i):
            correct += 1

    print(f"✅ Chroma accuracy: {correct}/{len(glove_vectors)} = {correct/len(glove_vectors)*100:.2f}%")

# -------------------
# Weaviate Verification
# -------------------
def verify_weaviate():
    import weaviate

    client = weaviate.connect_to_local(host="localhost", port=8080, grpc_port=50051)

    collection = client.collections.get("VectorDocGlove")

    correct = 0
    total = len(glove_vectors)

    for i, vec in enumerate(glove_vectors):
        result = collection.query.near_vector(
            near_vector=vec.tolist(),
            limit=1,
            return_properties=["word"],
            include_vector_distance=True 
        )

        if result.objects and result.objects[0].properties["word"] == words[i]:
            correct += 1

    accuracy = correct / total * 100
    print(f"✅ Weaviate accuracy: {correct}/{total} = {accuracy:.2f}%")

    client.close()


# -------------------
# pgvector Verification
# -------------------
def verify_pgvector():
    conn = psycopg2.connect(
        dbname="vectors", user="postgres", password="password", host="localhost", port=5432
    )
    cur = conn.cursor()

    correct = 0
    for i, vec in enumerate(glove_vectors):
        py_vec = [float(x) for x in vec]
        cur.execute(
            "SELECT word FROM items_glove ORDER BY embedding <-> %s::vector LIMIT 1;",
            (py_vec,)
        )
        nearest = cur.fetchone()
        if nearest and nearest[0] == glove_words[i]:
            correct += 1

    cur.close()
    conn.close()
    print(f"✅ pgvector accuracy: {correct}/{len(glove_vectors)} = {correct/len(glove_vectors)*100:.2f}%")

# -------------------
# MAIN
# -------------------
if __name__ == "__main__":
    print("🔍 Verifying top-1 accuracy against 1000 GloVe word vectors...")
    verify_qdrant()
    verify_chroma()
    verify_weaviate()
    verify_pgvector()
