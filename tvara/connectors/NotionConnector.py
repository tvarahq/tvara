import requests
from .base import BaseConnector
from typing import Dict, Any, Union

class NotionConnector(BaseConnector):
    def __init__(self, token: str):
        super().__init__(name="Notion", token=token)
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

    def get_action_schema(self):
        return {
            "get_page": {
                "description": "Fetch the content of a Notion page",
                "parameters": {
                    "page_id": {"type": "string", "required": True, "description": "The ID of the Notion page"}
                },
                "example_use_case": "User says 'get my notes from xyz page'"
            },
            "search": {
                "description": "Search for pages or databases matching a query",
                "parameters": {
                    "query": {"type": "string", "required": True, "description": "Search keyword"}
                },
                "example_use_case": "User says 'search for project plan'"
            },
            "list_user_databases": {
                "description": "List all databases the user has access to",
                "parameters": {},
                "example_use_case": "User says 'show all my databases'"
            },
            "list_all_pages": {
                "description": "List all pages in a Notion database",
                "parameters": {
                    "database_id": {"type": "string", "required": True, "description": "The ID of the Notion database"}
                },
                "example_use_case": "User says 'list all pages in my tasks database'"
            }
        }

    def run(self, action: str, input: dict) -> Union[Dict[str, Any], str]:
        if action == "get_page":
            page_id = input.get("page_id")
            if not page_id:
                return {"error": "Missing 'page_id'"}
            response = requests.get(f"{self.base_url}/pages/{page_id}", headers=self.headers)
            return response.json() if response.ok else {"error": response.text}

        elif action == "search":
            query = input.get("query")
            if not query:
                return {"error": "Missing 'query'"}
            data = {"query": query}
            response = requests.post(f"{self.base_url}/search", headers=self.headers, json=data)
            return response.json() if response.ok else {"error": response.text}
        
        elif action == "list_user_databases":
            response = requests.post(f"{self.base_url}/search", headers=self.headers, json={"filter": {"property": "object", "value": "database"}})
            if not response.ok:
                return {"error": response.text}
            
            data = response.json()
            databases = []
            for db in data.get("results", []):
                db_id = db.get("id")
                title = "Untitled"
                title_prop = db.get("title", [])
                if title_prop:
                    title = title_prop[0].get("plain_text", "Untitled")
                databases.append({"id": db_id, "title": title})
            
            return {"databases": databases}

        elif action == "list_all_pages":
            database_id = input.get("database_id")
            if not database_id:
                return {"error": "Missing 'database_id'"}

            all_pages = []
            has_more = True
            next_cursor = None

            while has_more:
                payload = {"page_size": 100}
                if next_cursor:
                    payload["start_cursor"] = next_cursor

                response = requests.post(
                    f"{self.base_url}/databases/{database_id}/query",
                    headers=self.headers,
                    json=payload
                )
                if not response.ok:
                    return {"error": response.text}

                result = response.json()
                results = result.get("results", [])
                has_more = result.get("has_more", False)
                next_cursor = result.get("next_cursor")

                for page in results:
                    page_id = page.get("id")
                    properties = page.get("properties", {})
                    # Try to extract the title
                    title = "Untitled"
                    for prop in properties.values():
                        if prop.get("type") == "title":
                            title_arr = prop.get("title", [])
                            if title_arr:
                                title = title_arr[0].get("plain_text", "Untitled")
                            break
                    all_pages.append({"id": page_id, "title": title})

            return {"pages": all_pages}


        else:
            return {"error": f"Unknown action '{action}'"}
