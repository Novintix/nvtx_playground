# db.py
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from config import SQLITE_DB

Path("data").mkdir(exist_ok=True)


def get_connection():
    """Get SQLite connection"""
    return sqlite3.connect(SQLITE_DB)


def init_db():
    """Initialize database with enhanced schema"""
    conn = get_connection()
    cursor = conn.cursor()

    # Queries table with timestamp
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS queries (
        query TEXT PRIMARY KEY,
        query_hash TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        paper_count INTEGER DEFAULT 0
    )
    """)

    # Papers table with full metadata
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS papers (
        pmid TEXT PRIMARY KEY,
        query TEXT,
        title TEXT,
        abstract TEXT,
        journal TEXT,
        year INTEGER,
        citations INTEGER,
        final_score REAL,
        fetched_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (query) REFERENCES queries(query)
    )
    """)

    # LangChain conversation history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        query TEXT,
        answer TEXT,
        papers_used TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create indices
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_query ON papers(query)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_year ON papers(year)")

    conn.commit()
    conn.close()


def migrate_db():
    """Add missing columns to existing database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check and add paper_count to queries table
        cursor.execute("PRAGMA table_info(queries)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'paper_count' not in columns:
            print("⚠️ Adding missing paper_count column to queries table...")
            cursor.execute("ALTER TABLE queries ADD COLUMN paper_count INTEGER DEFAULT 0")
            conn.commit()
            print("✅ Successfully added paper_count column!")
        else:
            print("✅ queries table - paper_count column exists")
        
        # Check and add final_score to papers table
        cursor.execute("PRAGMA table_info(papers)")
        paper_columns = [col[1] for col in cursor.fetchall()]
        
        if 'final_score' not in paper_columns:
            print("⚠️ Adding missing final_score column to papers table...")
            cursor.execute("ALTER TABLE papers ADD COLUMN final_score REAL DEFAULT 0.0")
            conn.commit()
            print("✅ Successfully added final_score column!")
        else:
            print("✅ papers table - final_score column exists")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()


def query_exists(query: str) -> bool:
    """Check if query is cached"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM queries WHERE query=?", (query,))
    result = cur.fetchone()
    conn.close()
    return result is not None


def get_cached_papers(query: str) -> List[Dict]:
    """Retrieve cached papers for a query"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT pmid, title, abstract, journal, year, citations, final_score
        FROM papers 
        WHERE query=?
        ORDER BY final_score DESC
    """, (query,))
    
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "pmid": r[0],
            "title": r[1],
            "abstract": r[2],
            "journal": r[3],
            "year": r[4],
            "citations": r[5],
            "final_score": r[6] or 0.0
        }
        for r in rows
    ]


def cache_papers(query: str, papers: List[Dict]):
    """Cache papers with scores"""
    conn = get_connection()
    cur = conn.cursor()

    # Insert query
    cur.execute(
        "INSERT OR IGNORE INTO queries(query, paper_count) VALUES (?, ?)",
        (query, len(papers))
    )

    # Insert papers
    for p in papers:
        cur.execute("""
            INSERT OR REPLACE INTO papers 
            (pmid, query, title, abstract, journal, year, citations, final_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["pmid"], query, p["title"], p["abstract"],
            p["journal"], p["year"], p["citations"],
            p.get("final_score", 0.0)
        ))

    conn.commit()
    conn.close()


def save_conversation(session_id: str, query: str, answer: str, papers_used: List[str]):
    """Save conversation for LangChain memory"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO conversation_history (session_id, query, answer, papers_used)
        VALUES (?, ?, ?, ?)
    """, (session_id, query, answer, ",".join(papers_used)))
    
    conn.commit()
    conn.close()


def get_conversation_history(session_id: str, limit: int = 5) -> List[Dict]:
    """Retrieve conversation history"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT query, answer, timestamp 
        FROM conversation_history 
        WHERE session_id=?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (session_id, limit))
    
    rows = cur.fetchall()
    conn.close()
    
    return [{"query": r[0], "answer": r[1], "timestamp": r[2]} for r in rows]


def get_db_stats() -> Dict:
    """Get database statistics"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM queries")
    query_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM papers")
    paper_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(DISTINCT query) FROM papers")
    unique_queries = cur.fetchone()[0]
    
    conn.close()
    
    return {
        "total_queries": query_count,
        "total_papers": paper_count,
        "unique_queries": unique_queries
    }
    
    
    
#python -c "from db import migrate_db; migrate_db()"