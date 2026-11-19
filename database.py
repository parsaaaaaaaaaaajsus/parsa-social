import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


def get_database_url():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return database_url


def get_connection():
    return psycopg.connect(
        get_database_url(),
        row_factory=dict_row,
    )


def init_database():
    schema_path = Path(__file__).with_name("database.sql")
    schema = schema_path.read_text(encoding="utf-8")

    with psycopg.connect(get_database_url()) as conn:
        conn.execute(schema)
