# MongoDB Data Pipeline

Python + MongoDB learning repository.

## Focus Areas

- pymongo
- document modeling
- aggregation pipelines
- indexing
- migration concepts

## Usage

Install dependencies from `requirements.txt` and run the package as a module:

```bash
python -m src count users
python -m src top events event_type --limit 5
python -m src recent logs --days 3
```

The package separates connection, aggregation, and migration helpers into `src/connect.py`, `src/aggregations.py`, and `src/migrations.py`.

## Suggested Collections

- users
- events
- logs

## Recruiter Value

Shows backend breadth across SQL + NoSQL systems.
