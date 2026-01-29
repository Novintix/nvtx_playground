from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

@tool
def web_search_tool(query: str):
    """
    Searches the web for text results.
    """
    try:
        # SearchRun returns a simple string, easier for LLM to parse than SearchResults json
        search = DuckDuckGoSearchRun()
        return search.invoke(query)
    except Exception as e:
        return f"Error fetching search results: {str(e)}"

def get_tools():
    return [web_search_tool]