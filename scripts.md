# 🔁 CORRECTED MANUAL BACKUP (PowerShell)

## 🧠 1. **Create folders**

```powershell
mkdir backups\qdrant, backups\chroma, backups\weaviate, backups\pgvector
```

---

## 🧠 2. **Backup Qdrant**

**Create snapshot:**

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:6333/collections/test_glove/snapshots"
```

**Copy snapshot file:**

```powershell
docker exec qdrant ls /qdrant/snapshots/test_glove
```

```powershell
docker cp qdrant:/qdrant/snapshots/test_glove/test_glove-XXXXXXXXX.snapshot .\backups\qdrant\
```

---

## 🧠 3. **Backup Chroma**

**Copy volume contents to host:**

```powershell
docker run --rm -v chroma_data:/data -v "$(pwd)\backups\chroma:/backup" alpine sh -c "cp -r /data/. /backup/"
```

---

## 🧠 4. **Backup Weaviate**

````powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8080/v1/backups/filesystem" -Body '{"id": "backup_glove"}' -ContentType "application/json"
```

---

## 🧠 5. **Backup pgvector (Postgres)**
```powershell
docker exec pgvector pg_dump -U postgres -d vectors -F c -f /tmp/pgvector.dump
docker cp pgvector:/tmp/pgvector.dump ./backups/pgvector/
docker exec pgvector rm /tmp/pgvector.dump
````

---

# MANUAL RESTORE (PowerShell)

## 🧠 1. **Restore Qdrant**

**Copy snapshot back:**

```powershell
docker cp .\backups\qdrant\test_glove-XXXXX.snapshot qdrant:/tmp/test_glove-XXXXXXXXX.snapshot
```

**Recreate collection (if needed):**

```powershell
Invoke-RestMethod -Method PUT -Uri "http://localhost:6333/collections/test_glove" `
  -ContentType "application/json" `
  -Body '{
    "vectors": {
      "size": 100,
      "distance": "Cosine"
    }
  }'
```

**Restore from snapshot:**

```powershell
Invoke-RestMethod -Method PUT -Uri "http://localhost:6333/collections/test_glove/snapshots/recover" `
    -ContentType "application/json" `
    -Body '{"location":"file:///tmp/test_glove-XXXXXXXXXX.snapshot"}'

```

---

## 🧠 2. **Restore Chroma**

```powershell
docker stop chroma
```

```powershell
docker run --rm -v "$(pwd)\backups\chroma:/backup" -v chroma_data:/data alpine sh -c "cp -r /backup/. /data/ && chown -R 1000:1000 /data"
```

```powershell
docker start chroma
```

---

## 🧠 3. **Restore Weaviate**

```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8080/v1/backups/filesystem/backup_glove/restore" -Body '{"id": "backup_glove"}' -ContentType "application/json"

```

---

## 🧠 4. **Restore pgvector**

```powershell
docker exec -e PGPASSWORD=password pgvector dropdb -U postgres vectors
docker exec -e PGPASSWORD=password pgvector createdb -U postgres vectors
docker cp .\backups\pgvector\pgvector.dump pgvector:/tmp/pgvector.dump
docker exec -e PGPASSWORD=password pgvector pg_restore -U postgres -d vectors /tmp/pgvector.dump
```
