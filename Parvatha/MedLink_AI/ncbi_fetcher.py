# ncbi_fetcher.py
import os
from typing import List, Dict, Optional
from Bio import Entrez
import hashlib
import re
from config import MAX_PAPERS_DEFAULT
from db import query_exists, get_cached_papers, cache_papers
from error_handler import handle_error, log_info, log_warning
from dotenv import load_dotenv
  
load_dotenv()

# Configure Entrez
Entrez.email = os.getenv("NCBI_EMAIL", "user@example.com")
if os.getenv("NCBI_API_KEY"):
    Entrez.api_key = os.getenv("NCBI_API_KEY")


# ==================================================
# NEW: PubMed Query Preprocessor
# ==================================================
def preprocess_query_for_pubmed(query: str) -> str:
    """
    Convert natural language query to PubMed search syntax
    """
    if not query:
        return ""
    
    # If already has PubMed tags, return as-is
    if '[' in query and ']' in query:
        return query
    
    # Clean up
    query = query.strip().rstrip('?').strip()
    
    # Stop words to remove
    stop_words = {
        'what', 'are', 'the', 'is', 'how', 'does', 'do', 'in', 'of', 
        'with', 'for', 'to', 'and', 'or', 'a', 'an', 'this', 'that',
        'these', 'those', 'associated', 'related', 'changes', 'effect',
        'role', 'impact', 'between', 'among', 'within', 'during', 'on',
        'human', 'tissues', 'patients', 'study', 'studies', 'cells',
        'treatment', 'effect', 'clinical'
    }
    
    # Extract keywords
    words = query.lower().split()
    key_terms = [w for w in words if w not in stop_words and len(w) > 2]
    
    # Limit to 6 most important terms
    key_terms = key_terms[:6]
    
    if not key_terms:
        return query
    
    # Build PubMed query with [tiab] (Title/Abstract) tags
    tagged_terms = [f"{term}[tiab]" for term in key_terms]
    
    return " AND ".join(tagged_terms)


class NCBIFetcher:
    """Enhanced NCBI fetcher with smart caching"""
    
    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
    
    def _generate_query_hash(self, query: str) -> str:
        """Generate unique hash for query"""
        return hashlib.md5(query.strip().lower().encode()).hexdigest()
    
    def fetch_papers(
        self, 
        query: str, 
        max_results: int = MAX_PAPERS_DEFAULT,
        use_cache: bool = True
    ) -> List[Dict]:
        """
        Fetch papers from NCBI with intelligent caching
        """
        try:
            # FIX: Auto-convert natural language to PubMed syntax
            original_query = query
            query = preprocess_query_for_pubmed(query)
            
            if original_query != query:
                log_info(f"🔍 Query converted: '{original_query[:60]}...' → '{query}'")
            
            # Validation
            if not query or not isinstance(query, str):
                raise ValueError("Query must be a non-empty string")
            
            query = query.strip().strip('"').strip("'")
            
            if not query:
                return []
            
            # Check cache first
            if use_cache and query_exists(query):
                log_info("📦 Cache HIT - Using cached papers")
                self.cache_hits += 1
                papers = get_cached_papers(query)
                
                if papers:
                    log_info(f"✅ Retrieved {len(papers)} cached papers")
                    return papers
            
            # Cache miss - fetch from NCBI
            log_info(f"🔍 Cache MISS - Fetching from NCBI: '{query[:50]}...'")
            self.cache_misses += 1
            
            # Search PubMed
            search_handle = Entrez.esearch(
                db="pubmed",
                term=query,
                retmax=max_results,
                sort="relevance"
            )
            search_results = Entrez.read(search_handle)
            search_handle.close()
            
            pmids = search_results.get("IdList", [])
            
            # If no results, try with simplified query (take first part)
            if not pmids and " AND " in query:
                simplified = query.split(" AND ")[0].strip()
                if simplified != query:
                    log_warning(f"🔁 Retrying with simplified query: {simplified}")
                    return self.fetch_papers(simplified, max_results, use_cache=False)
            
            # If still no results, try with OR instead of AND
            if not pmids and " AND " in query:
                simplified = query.replace(" AND ", " OR ")
                log_warning(f"🔁 Retrying with OR query: {simplified}")
                return self.fetch_papers(simplified, max_results, use_cache=False)
            
            if not pmids:
                log_warning(f"⚠️ No PMIDs found for query: {query}")
                return []
            
            log_info(f"📚 Found {len(pmids)} papers, fetching details...")
            
            # Fetch paper details
            papers = self._fetch_paper_details(pmids, query)
            
            # Cache results
            if papers:
                cache_papers(query, papers)
                log_info(f"✅ Cached {len(papers)} papers")
            
            return papers
            
        except Exception as e:
            error_msg = handle_error(e, "fetch_papers")
            log_warning(error_msg)
            
            # Try to return cached results as fallback
            if query and query_exists(query):
                log_info("⚠️ Returning cached results as fallback")
                return get_cached_papers(query)
            
            return []
    
    def _fetch_paper_details(self, pmids: List[str], query: str) -> List[Dict]:
        """Fetch detailed paper information"""
        try:
            batch_size = 50
            all_papers = []
            
            for i in range(0, len(pmids), batch_size):
                batch_pmids = pmids[i:i + batch_size]
                
                fetch_handle = Entrez.efetch(
                    db="pubmed",
                    id=",".join(batch_pmids),
                    rettype="abstract",
                    retmode="xml"
                )
                
                records = Entrez.read(fetch_handle)
                fetch_handle.close()
                
                # Parse papers
                for article in records.get("PubmedArticle", []):
                    paper = self._parse_article(article, query)
                    if paper:
                        all_papers.append(paper)
            
            return all_papers
            
        except Exception as e:
            log_warning(f"⚠️ Error fetching paper details: {e}")
            return []
    
    def _parse_article(self, article: Dict, query: str) -> Optional[Dict]:
        """Parse PubMed article into structured format"""
        try:
            medline = article.get("MedlineCitation", {})
            article_data = medline.get("Article", {})
            
            # Extract PMID
            pmid = str(medline.get("PMID", ""))
            if not pmid:
                return None
            
            # Extract title
            title = article_data.get("ArticleTitle", "")
            if not title:
                return None
            
            # Extract abstract
            abstract_data = article_data.get("Abstract", {})
            abstract_text = ""
            
            if "AbstractText" in abstract_data:
                abstract_parts = abstract_data["AbstractText"]
                if isinstance(abstract_parts, list):
                    abstract_text = " ".join([str(part) for part in abstract_parts])
                else:
                    abstract_text = str(abstract_parts)
            
            # Extract journal info
            journal_data = article_data.get("Journal", {})
            journal_title = journal_data.get("Title", "Unknown Journal")
            
            # Extract year
            pub_date = journal_data.get("JournalIssue", {}).get("PubDate", {})
            year = 0
            
            if "Year" in pub_date:
                try:
                    year = int(pub_date["Year"])
                except (ValueError, TypeError):
                    year = 0
            elif "MedlineDate" in pub_date:
                try:
                    year = int(pub_date["MedlineDate"][:4])
                except (ValueError, TypeError):
                    year = 0
            
            # Create paper dict
            paper = {
                "pmid": pmid,
                "title": title,
                "abstract": abstract_text,
                "journal": journal_title,
                "year": year,
                "authors": [],
                "citations": 0,
                "query": query
            }
            
            return paper
            
        except Exception as e:
            log_warning(f"⚠️ Error parsing article: {e}")
            return None
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_requests": total,
            "hit_rate": round(hit_rate, 2)
        }


# ==================================================
# Test the fix when running directly
# ==================================================
if __name__ == "__main__":
    print("Testing PubMed query preprocessor:\n")
    
    test_queries = [
        "What are the epigenetic changes associated with aging in human tissues?",
        "How does metformin affect cancer progression?",
        "What is the role of gut microbiome in Alzheimer's disease?",
        "Does aspirin reduce cardiovascular disease risk?"
    ]
    
    for q in test_queries:
        pubmed_q = preprocess_query_for_pubmed(q)
        print(f"User:   {q}")
        print(f"PubMed: {pubmed_q}\n")
    
    # Test actual fetch
    print("=" * 60)
    print("Testing NCBI fetch:")
    fetcher = NCBIFetcher()
    
    test_q = "What are the epigenetic changes associated with aging in human tissues?"
    papers = fetcher.fetch_papers(test_q, max_results=5)
    
    print(f"\n✅ Found {len(papers)} papers for: '{test_q}'")
    for i, p in enumerate(papers[:3], 1):
        print(f"\n{i}. {p['title']}")
        print(f"   PMID: {p['pmid']} | Year: {p['year']} | Journal: {p['journal'][:30]}...")