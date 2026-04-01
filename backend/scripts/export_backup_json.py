"""
Esporta TUTTE le collection da MongoDB Atlas in file JSON leggibili.
Crea anche un file unico completo (all_data.json) e un indice.
"""
import json
import os
from datetime import datetime, timezone
from pymongo import MongoClient
from bson import Binary, ObjectId

ATLAS_URI = "mongodb+srv://fandrex1_db_user:Cineworld123@cluster0.6q21tmr.mongodb.net/cineworld?retryWrites=true&w=majority"
DB_NAME = "cineworld"
OUTPUT_DIR = "/app/backup_produzione"

# Collections con dati binari (poster) che vanno gestiti diversamente
BINARY_COLLECTIONS = {"poster_files"}


def make_serializable(obj):
    """Converte oggetti MongoDB non serializzabili in tipi JSON."""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, Binary):
        return f"<binary:{len(obj)} bytes>"
    if isinstance(obj, bytes):
        return f"<binary:{len(obj)} bytes>"
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_serializable(i) for i in obj]
    return obj


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    client = MongoClient(ATLAS_URI)
    db = client[DB_NAME]

    collection_names = sorted(db.list_collection_names())
    log(f"Trovate {len(collection_names)} collection da esportare")

    index = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "database": DB_NAME,
        "collections": {}
    }
    all_data = {}

    for coll_name in collection_names:
        count = db[coll_name].count_documents({})
        if count == 0:
            index["collections"][coll_name] = {"count": 0, "file": None}
            continue

        if coll_name in BINARY_COLLECTIONS:
            # Per poster_files: salva metadati senza il campo binario 'data'
            docs = list(db[coll_name].find({}, {"data": 0}))
            docs = [make_serializable(d) for d in docs]
            filename = f"{coll_name}_metadata.json"
        elif coll_name == "people" and count > 5000:
            # Collection 'people' molto grande: salva solo un campione
            docs = list(db[coll_name].find({}).limit(100))
            docs = [make_serializable(d) for d in docs]
            filename = f"{coll_name}_sample100.json"
            log(f"  {coll_name}: {count} docs (salvato campione di 100)")
        else:
            docs = list(db[coll_name].find({}))
            docs = [make_serializable(d) for d in docs]
            filename = f"{coll_name}.json"

        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=2, default=str)

        size_kb = os.path.getsize(filepath) / 1024
        index["collections"][coll_name] = {
            "count": len(docs),
            "total_in_db": count,
            "file": filename,
            "size_kb": round(size_kb, 1)
        }
        all_data[coll_name] = docs
        log(f"  {coll_name}: {len(docs)} docs → {filename} ({size_kb:.1f} KB)")

    # Salva indice
    index_path = os.path.join(OUTPUT_DIR, "_INDEX.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    log(f"\nIndice salvato: _INDEX.json")

    # Salva file unico completo (escluso people e poster binari)
    all_data_clean = {k: v for k, v in all_data.items() if k not in ("people",)}
    all_path = os.path.join(OUTPUT_DIR, "ALL_DATA.json")
    with open(all_path, "w", encoding="utf-8") as f:
        json.dump(all_data_clean, f, ensure_ascii=False, indent=2, default=str)
    size_mb = os.path.getsize(all_path) / (1024 * 1024)
    log(f"File completo: ALL_DATA.json ({size_mb:.1f} MB)")

    # Riepilogo
    total_files = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".json")])
    total_size = sum(
        os.path.getsize(os.path.join(OUTPUT_DIR, f))
        for f in os.listdir(OUTPUT_DIR)
    ) / (1024 * 1024)
    log(f"\nBackup completato: {total_files} file, {total_size:.1f} MB totali")
    log(f"Directory: {OUTPUT_DIR}")

    client.close()


if __name__ == "__main__":
    main()
