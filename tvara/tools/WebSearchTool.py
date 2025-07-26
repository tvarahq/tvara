from .BaseTool import BaseTool
from tavily import TavilyClient

class WebSearchTool(BaseTool):
    def __init__(self, api_key: str):
        super().__init__(name="web_search_tool", description="Performs a web search and returns results.")
        self.client = TavilyClient(api_key=api_key)

    def run(self, input_data: str) -> str:
        response = self.client.search(query=input_data)
        return str(response)