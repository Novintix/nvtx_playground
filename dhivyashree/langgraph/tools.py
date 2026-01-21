from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import Tool
import os

def get_search_tool():
    """Returns the Tavily search tool."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("WARNING: TAVILY_API_KEY not found in environment variables.")
        return None
    
    return TavilySearchResults(tavily_api_key=api_key, max_results=3)
