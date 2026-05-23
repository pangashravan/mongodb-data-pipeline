import argparse
import json
import sys
from typing import Any, Dict, Optional

from pymongo.errors import ServerSelectionTimeoutError

from .aggregations import (
    collection_summary,
    count_documents,
    recent_documents,
    top_values_by_count,
)
from .connect import create_client, get_database
from .migrations import (
    add_missing_field,
    copy_collection,
    ensure_index,
    migrate_string_field_to_lowercase,
    rename_field,
)


def parse_json_arg(value: str) -> Dict[str, Any]:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"Invalid JSON: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run MongoDB aggregation and migration helpers.",
    )
    parser.add_argument(
        "--uri",
        help="MongoDB URI. Falls back to MONGO_URI from .env or localhost.",
    )
    parser.add_argument(
        "--db",
        dest="db_name",
        help="Database name. Defaults to MONGO_DB from .env or mongodb_data_pipeline.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    count = subparsers.add_parser("count", help="Count documents in a collection.")
    count.add_argument("collection", help="Collection name.")
    count.add_argument("--match", type=parse_json_arg, help="JSON filter for the count.")

    top = subparsers.add_parser("top", help="Show top values by count.")
    top.add_argument("collection", help="Collection name.")
    top.add_argument("field", help="Field to group by.")
    top.add_argument("--match", type=parse_json_arg, help="Optional JSON filter.")
    top.add_argument("--limit", type=int, default=10, help="How many values to return.")

    recent = subparsers.add_parser("recent", help="Show recent documents in a collection.")
    recent.add_argument("collection", help="Collection name.")
    recent.add_argument("--date-field", default="created_at", help="Date field name.")
    recent.add_argument("--days", type=int, default=7, help="How many days back to query.")
    recent.add_argument("--limit", type=int, default=25, help="Maximum documents to return.")

    summary = subparsers.add_parser("summary", help="Summarize a collection.")
    summary.add_argument("collection", help="Collection name.")
    summary.add_argument("--sample-size", type=int, default=10, help="Sample document count.")

    index = subparsers.add_parser("ensure-index", help="Create an index on a collection.")
    index.add_argument("collection", help="Collection name.")
    index.add_argument(
        "keys",
        help="Index keys as JSON list of tuples, e.g. [[\"field\", 1]].",
        type=parse_json_arg,
    )
    index.add_argument("--unique", action="store_true", help="Create a unique index.")
    index.add_argument("--sparse", action="store_true", help="Create a sparse index.")

    rename = subparsers.add_parser("rename-field", help="Rename a field on matched documents.")
    rename.add_argument("collection", help="Collection name.")
    rename.add_argument("old", help="Old field name.")
    rename.add_argument("new", help="New field name.")
    rename.add_argument("--match", type=parse_json_arg, help="Optional JSON filter.")

    add_field = subparsers.add_parser("add-field", help="Add a missing field to documents.")
    add_field.add_argument("collection", help="Collection name.")
    add_field.add_argument("field", help="Field name to add.")
    add_field.add_argument("value", help="Default value to set.")
    add_field.add_argument("--match", type=parse_json_arg, help="Optional JSON filter.")

    lower = subparsers.add_parser(
        "lowercase-field",
        help="Lowercase string values for a field.",
    )
    lower.add_argument("collection", help="Collection name.")
    lower.add_argument("field", help="Field name to lowercase.")
    lower.add_argument("--match", type=parse_json_arg, help="Optional JSON filter.")

    copy = subparsers.add_parser("copy", help="Copy documents between collections.")
    copy.add_argument("source", help="Source collection name.")
    copy.add_argument("target", help="Target collection name.")
    copy.add_argument(
        "--target-db",
        dest="target_db",
        help="Optional target database name.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        client = create_client(args.uri) if args.uri else create_client()
        database = get_database(client=client, db_name=args.db_name)
    except ServerSelectionTimeoutError as exc:
        print(f"Unable to connect to MongoDB: {exc}", file=sys.stderr)
        return 2

    if args.command == "count":
        value = count_documents(database[args.collection], args.match)
        print(value)
        return 0

    if args.command == "top":
        results = top_values_by_count(
            database[args.collection], args.field, match=args.match, limit=args.limit
        )
        print(json.dumps(results, default=str, indent=2))
        return 0

    if args.command == "recent":
        results = recent_documents(
            database[args.collection],
            date_field=args.date_field,
            days=args.days,
            limit=args.limit,
        )
        print(json.dumps(results, default=str, indent=2))
        return 0

    if args.command == "summary":
        summary = collection_summary(database[args.collection], sample_size=args.sample_size)
        print(json.dumps(summary, default=str, indent=2))
        return 0

    if args.command == "ensure-index":
        index_name = ensure_index(database[args.collection], args.keys, unique=args.unique, sparse=args.sparse)
        print(index_name)
        return 0

    if args.command == "rename-field":
        count = rename_field(database[args.collection], args.old, args.new, filter=args.match)
        print(count)
        return 0

    if args.command == "add-field":
        count = add_missing_field(database[args.collection], args.field, args.value, filter=args.match)
        print(count)
        return 0

    if args.command == "lowercase-field":
        count = migrate_string_field_to_lowercase(database[args.collection], args.field, filter=args.match)
        print(count)
        return 0

    if args.command == "copy":
        target_db = database if args.target_db is None else get_database(client=client, db_name=args.target_db)
        inserted = copy_collection(database, args.source, target_db, args.target)
        print(inserted)
        return 0

    parser.print_help()
    return 1
