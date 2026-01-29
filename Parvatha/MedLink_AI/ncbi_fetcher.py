# ncbi_fetcher.py
from typing import List, Dict, Optional
from Bio import Entrez
import hashlib
from config import NCBI_EMAIL, NCBI_API_KEY, MAX_PAPERS_DEFAULT
from db import query_exists, get_cached_papers, cache_papers
from error_handler import handle_error, log_info, log_warning

# Configure Entrez
Entrez.email = NCBI_EMAIL
if NCBI_API_KEY:
    Entrez.api_key = NCBI_API_KEY


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
        
        Args:
            query: Search query
            max_results: Maximum papers to fetch
            use_cache: Whether to use cached results
            
        Returns:
            List of paper dictionaries
        """
        try:
            # Validate query
            if not query or not isinstance(query, str):
                raise ValueError("Query must be a non-empty string")
            
            query = query.strip()
            
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
            
            if not pmids:
                log_warning(f"📭 No papers found for query: '{query}'")
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
            if query_exists(query):
                log_info("⚠️ Returning cached results as fallback")
                return get_cached_papers(query)
            
            return []
    
    def _fetch_paper_details(self, pmids: List[str], query: str) -> List[Dict]:
        """Fetch detailed paper information"""
        try:
            # Fetch in batches to avoid timeouts
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
                # Try to extract year from MedlineDate (e.g., "2023 Jan-Feb")
                try:
                    year = int(pub_date["MedlineDate"][:4])
                except (ValueError, TypeError):
                    year = 0
            
            # Extract authors
            authors = []
            author_list = article_data.get("AuthorList", [])
            for author in author_list[:5]:  # First 5 authors
                last_name = author.get("LastName", "")
                initials = author.get("Initials", "")
                if last_name:
                    authors.append(f"{last_name} {initials}".strip())
            
            # Create paper dict
            paper = {
                "pmid": pmid,
                "title": title,
                "abstract": abstract_text,
                "journal": journal_title,
                "year": year,
                "authors": authors,
                "citations": 0,  # PubMed doesn't provide citation counts directly
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