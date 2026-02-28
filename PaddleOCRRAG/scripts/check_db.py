import chromadb
from pathlib import Path
import json

db_path = Path('data/chroma_db')
print(f'DB Path exists: {db_path.exists()}')

if db_path.exists():
    client = chromadb.PersistentClient(path=str(db_path))
    collections = client.list_collections()
    print(f'Collections: {len(collections)}')
    for coll in collections:
        print(f'  - {coll.name}: {coll.count()} docs')
        if coll.count() > 0:
            results = coll.get(limit=3, include=["documents"])
            for i, doc in enumerate(results["documents"][:3]):
                print(f'    [{i+1}] {doc[:80]}...' if len(doc) > 80 else f'    [{i+1}] {doc}')

rules_path = Path('data/rules')
print(f'\nRules path exists: {rules_path.exists()}')
if rules_path.exists():
    for f in rules_path.glob('*'):
        if f.is_file():
            print(f'  - {f.name} ({f.stat().st_size} bytes)')

meta_path = Path('data/document_meta.json')
print(f'\nMeta file exists: {meta_path.exists()}')
if meta_path.exists():
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    print(f'Registered docs: {len(meta)}')
    for doc_id, info in meta.items():
        print(f'  - {info.get("original_name")}: enabled={info.get("enabled")}')
