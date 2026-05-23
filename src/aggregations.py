from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

from pymongo.collection import Collection


def count_documents(collection: Collection, filter: Optional[Dict[str, Any]] = None) -> int:
    return collection.count_documents(filter or {})


def top_values_by_count(
    collection: Collection,
    field: str,
    match: Optional[Dict[str, Any]] = None,
    limit: int = 10,
    sort_desc: bool = True,
) -> List[Dict[str, Any]]:
    pipeline: List[Dict[str, Any]] = []
    if match:
        pipeline.append({"$match": match})
    pipeline.extend(
        [
            {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
            {"$sort": {"count": -1 if sort_desc else 1}},
            {"$limit": limit},
        ]
    )
    return list(collection.aggregate(pipeline))


def recent_documents(
    collection: Collection,
    date_field: str = "created_at",
    days: int = 7,
    sort_field: str = "created_at",
    limit: int = 25,
) -> List[Dict[str, Any]]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    pipeline = [
        {"$match": {date_field: {"$gte": cutoff}}},
        {"$sort": {sort_field: -1}},
        {"$limit": limit},
    ]
    return list(collection.aggregate(pipeline))


def field_histogram(
    collection: Collection,
    field: str,
    match: Optional[Dict[str, Any]] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    return top_values_by_count(collection, field=field, match=match, limit=limit)


def collection_summary(collection: Collection, sample_size: int = 10) -> Dict[str, Any]:
    return {
        "count": count_documents(collection),
        "sample": list(collection.find().limit(sample_size)),
    }
