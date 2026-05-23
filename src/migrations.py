from typing import Any, Dict, Iterable, List, Optional, Tuple

from pymongo import UpdateOne
from pymongo.collection import Collection
from pymongo.database import Database


def ensure_index(
    collection: Collection,
    keys: List[Tuple[str, int]],
    unique: bool = False,
    sparse: bool = False,
) -> str:
    return collection.create_index(keys, unique=unique, sparse=sparse)


def rename_field(
    collection: Collection,
    old_name: str,
    new_name: str,
    filter: Optional[Dict[str, Any]] = None,
) -> int:
    result = collection.update_many(filter or {}, {"$rename": {old_name: new_name}})
    return result.modified_count


def add_missing_field(
    collection: Collection,
    field_name: str,
    default_value: Any = None,
    filter: Optional[Dict[str, Any]] = None,
) -> int:
    selector = filter or {field_name: {"$exists": False}}
    result = collection.update_many(selector, {"$set": {field_name: default_value}})
    return result.modified_count


def migrate_string_field_to_lowercase(
    collection: Collection,
    field_name: str,
    filter: Optional[Dict[str, Any]] = None,
    batch_size: int = 500,
) -> int:
    query = {field_name: {"$exists": True}}
    if filter:
        query.update(filter)

    operations: List[UpdateOne] = []
    count = 0
    for doc in collection.find(query, {field_name: 1}):
        value = doc.get(field_name)
        if isinstance(value, str):
            lower_value = value.strip().lower()
            if lower_value != value:
                operations.append(
                    UpdateOne({"_id": doc["_id"]}, {"$set": {field_name: lower_value}})
                )
        if len(operations) >= batch_size:
            result = collection.bulk_write(operations, ordered=False)
            count += result.modified_count
            operations.clear()
    if operations:
        result = collection.bulk_write(operations, ordered=False)
        count += result.modified_count
    return count


def copy_collection(
    source_db: Database,
    source_name: str,
    target_db: Database,
    target_name: str,
    batch_size: int = 500,
) -> int:
    source = source_db[source_name]
    target = target_db[target_name]
    inserted = 0
    buffer: List[Dict[str, Any]] = []

    for doc in source.find():
        buffer.append(doc)
        if len(buffer) >= batch_size:
            target.insert_many(buffer, ordered=False)
            inserted += len(buffer)
            buffer.clear()
    if buffer:
        target.insert_many(buffer, ordered=False)
        inserted += len(buffer)
    return inserted


def reserve_collection_name(database: Database, base_name: str) -> str:
    if base_name not in database.list_collection_names():
        return base_name
    suffix = 1
    while f"{base_name}_{suffix}" in database.list_collection_names():
        suffix += 1
    return f"{base_name}_{suffix}"
