import os
from tavily import TavilyClient

_client = None

def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not set in .env")
        _client = TavilyClient(api_key=api_key)
    return _client

def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using Tavily and return formatted results."""
    try:
        client = _get_client()
        response = client.search(query, max_results=max_results)
        results = response.get("results", [])

        if not results:
            return "No results found."

        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(
                f"[{i}] {r.get('title', '')}\n{r.get('content', '')}\nURL: {r.get('url', '')}"
            )

        return "\n\n".join(formatted)

    except Exception as e:
        return f"Search failed: {str(e)}"