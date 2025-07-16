import subprocess
import time
import os

log_file = "restore_timings.log"
backup_path = os.path.abspath("./backups")

def log(msg):
    print(msg)
    with open(log_file, "a",encoding='utf-8') as f:
        f.write(msg + "\n")

def time_restore(name, restore_fn):
    log(f"▶️ Restoring {name}...")
    start = time.time()
    restore_fn()
    duration = time.time() - start
    log(f"""
        ===============================================================
        ✅ {name} restored in {duration:.2f} seconds.
        ===============================================================\n""")

# ---------------------
# Restore Commands
# ---------------------

def restore_qdrant():
    snapshot = "test_glove-6973768125926727-2025-07-16-14-50-26.snapshot"  # Replace with actual name
    subprocess.run([
        "docker", "cp", f"{backup_path}/qdrant/{snapshot}", f"qdrant:/tmp/{snapshot}"
    ])
    subprocess.run([
        "curl", "-X", "PUT", "http://localhost:6333/collections/test_glove",
        "-H", "Content-Type: application/json",
        "-d", '{"vectors":{"size":100,"distance":"Cosine"}}'
    ])
    subprocess.run([
        "curl", "-X", "PUT", "http://localhost:6333/collections/test_glove/snapshots/recover",
        "-H", "Content-Type: application/json",
        "-d", f'{{"location":"file:///tmp/{snapshot}"}}'
    ])

def restore_chroma():
    subprocess.run(["docker", "stop", "chroma"])
    subprocess.run([
        "docker", "run", "--rm",
        "-v", f"{backup_path}/chroma:/backup",
        "-v", "chroma_data:/data",
        "alpine", "sh", "-c", "cp -r /backup/. /data/ && chown -R 1000:1000 /data"
    ])
    subprocess.run(["docker", "start", "chroma"])

def restore_weaviate():
    subprocess.run([
        "curl", "-X", "POST", "http://localhost:8080/v1/backups/filesystem/backup_glove/restore",
        "-H", "Content-Type: application/json",
        "-d", '{"id": "backup_glove"}'
    ])

def restore_pgvector():
    subprocess.run([
        "docker", "exec", "-e", "PGPASSWORD=password", "pgvector",
        "dropdb", "-U", "postgres", "vectors"
    ])
    subprocess.run([
        "docker", "exec", "-e", "PGPASSWORD=password", "pgvector",
        "createdb", "-U", "postgres", "vectors"
    ])
    subprocess.run([
        "docker", "cp", f"{backup_path}/pgvector/pgvector.dump", "pgvector:/tmp/pgvector.dump"
    ])
    subprocess.run([
        "docker", "exec", "-e", "PGPASSWORD=password", "pgvector",
        "pg_restore", "-U", "postgres", "-d", "vectors", "/tmp/pgvector.dump"
    ])

# ---------------------
# Run Timed Restores
# ---------------------
if __name__ == "__main__":
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("🕒 Recovery Time Log\n====================\n\n")

    time_restore("Qdrant", restore_qdrant)
    time_restore("Chroma", restore_chroma)
    time_restore("Weaviate", restore_weaviate)
    time_restore("pgvector", restore_pgvector)

    log("✅ All restores completed.")
