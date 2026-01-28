# ncbi_fetcher.py
from Bio import Entrez
from config import NCBI_EMAIL, NCBI_API_KEY
from db import query_exists, get_connection
from error_handler import handle_error

Entrez.email = NCBI_EMAIL
if NCBI_API_KEY:
    Entrez.api_key = NCBI_API_KEY


def fetch_papers(query, max_results=25):
    try:
        if query_exists(query):
            print("📦 Using cached papers for this query")
            return fetch_cached_papers(query)

        print("🔍 Fetching papers from NCBI...")
        handle = Entrez.esearch(
            db="pubmed",
            term=query,
            retmax=max_results
        )
        record = Entrez.read(handle)
        pmids = record["IdList"]

        papers = []

        fetch_handle = Entrez.efetch(
            db="pubmed",
            id=",".join(pmids),
            rettype="abstract",
            retmode="xml"
        )
        records = Entrez.read(fetch_handle)

        for article in records["PubmedArticle"]:
            medline = article["MedlineCitation"]
            article_data = medline["Article"]

            paper = {
                "pmid": medline["PMID"],
                "title": article_data["ArticleTitle"],
                "abstract": article_data["Abstract"]["AbstractText"][0] if "Abstract" in article_data else "",
                "journal": article_data["Journal"]["Title"],
                "year": int(article_data["Journal"]["JournalIssue"]["PubDate"].get("Year", 0)),
                "citations": 0  # Placeholder (PubMed doesn't give citations directly)
            }

            papers.append(paper)

        cache_papers(query, papers)
        return papers

    except Exception as e:
        raise RuntimeError(handle_error(e))


def cache_papers(query, papers):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("INSERT OR IGNORE INTO queries(query) VALUES (?)", (query,))

    for p in papers:
        cur.execute("""
        INSERT OR IGNORE INTO papers VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (p["pmid"], query, p["title"], p["abstract"], p["journal"], p["year"], p["citations"]))

    conn.commit()
    conn.close()


def fetch_cached_papers(query):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT pmid, title, abstract, journal, year, citations FROM papers WHERE query=?", (query,))
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "pmid": r[0],
            "title": r[1],
            "abstract": r[2],
            "journal": r[3],
            "year": r[4],
            "citations": r[5]
        }
        for r in rows
    ]
