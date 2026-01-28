from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool

@tool
def web_search_tool(query: str):
    """
    Searches for recent interview questions and returns specific links.
    Returns a list of results with Title, Snippet, and URL.
    """
    # backend="news" helps find recent articles/blogs
    search = DuckDuckGoSearchResults(backend="news", num_results=3) 
    return search.run(query)

def get_tools():
    return [web_search_tool]