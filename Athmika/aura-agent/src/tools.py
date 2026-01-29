from langchain_tavily import TavilySearch
from langchain_core.tools import tool

@tool
def web_search_tool(query: str):
    """
    Searches for real interview experiences using Tavily.
    Returns a list of dictionaries with 'url' and 'content'.
    """
    try:
        # max_results=3 ensures we get the top 3 blog posts
        tool = TavilySearch(
            max_results=3,
            search_depth="advanced" # 'advanced' finds high-quality blogs
        )
        # The tool expects a dictionary input for the query
        return tool.invoke({"query": query})
    except Exception as e:
        return f"Search Error: {str(e)}"

def get_tools():
    return [web_search_tool]