import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name, default)
    return value if value is not None else default


def get_mongo_uri() -> str:
    return get_env("MONGO_URI", "mongodb://localhost:27017") or "mongodb://localhost:27017"


def get_database_name() -> str:
    return get_env("MONGO_DB", "mongodb_data_pipeline") or "mongodb_data_pipeline"


def create_client(uri: Optional[str] = None, timeout_ms: int = 5000) -> MongoClient:
    uri = uri or get_mongo_uri()
    return MongoClient(uri, serverSelectionTimeoutMS=timeout_ms)


def get_database(client: Optional[MongoClient] = None, db_name: Optional[str] = None) -> Database:
    client = client or create_client()
    return client[db_name or get_database_name()]
