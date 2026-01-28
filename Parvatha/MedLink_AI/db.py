# db.py
import sqlite3
from pathlib import Path
from config import SQLITE_DB

Path("data").mkdir(exist_ok=True)

def get_connection():
    return sqlite3.connect(SQLITE_DB)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS queries (
        query TEXT PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS papers (
        pmid TEXT PRIMARY KEY,
        query TEXT,
        title TEXT,
        abstract TEXT,
        journal TEXT,
        year INTEGER,
        citations INTEGER
    )
    """)

    conn.commit()
    conn.close()

def query_exists(query):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM queries WHERE query=?", (query,))
    result = cur.fetchone()
    conn.close()
    return result is not None

#test run
#python -c "from db import init_db; init_db(); print('DB OK')"
