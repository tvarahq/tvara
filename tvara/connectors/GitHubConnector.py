import requests
from .base import BaseConnector

class GitHubConnector(BaseConnector):
    def __init__(self, name: str, token: str):
        super().__init__(name)
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }

    def get_action_schema(self) -> dict:
        return {
            "list_repos": {},
            "list_issues": {"owner": "string", "repo": "string"},
            "create_issue_comment": {
                "owner": "string",
                "repo": "string",
                "issue_number": "integer",
                "comment": "string"
            },
            "get_repo_info": {
                "owner": "string",
                "repo": "string"
            }
        }

    def run(self, action: str, input: dict) -> str:
        if action == "list_repos":
            response = requests.get(f"{self.base_url}/user/repos", headers=self.headers)
            return response.json()

        elif action == "list_issues":
            owner = input.get("owner")
            repo = input.get("repo")
            if not owner or not repo:
                return "Error: 'owner' and 'repo' are required for 'list_issues' action."
            response = requests.get(f"{self.base_url}/repos/{owner}/{repo}/issues", headers=self.headers)
            return response.json()

        elif action == "create_issue_comment":
            owner = input.get("owner")
            repo = input.get("repo")
            issue_number = input.get("issue_number")
            comment = input.get("comment")
            if not owner or not repo or issue_number is None or not comment:
                return "Error: 'owner', 'repo', 'issue_number', and 'comment' are required for 'create_issue_comment' action."
            data = {"body": comment}
            response = requests.post(f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments", json=data, headers=self.headers)
            return response.json()
        
        elif action == "get_repo_info":
            owner = input.get("owner")
            repo = input.get("repo")
            if not owner or not repo:
                return "Error: 'owner' and 'repo' are required for 'get_repo_info' action."

            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

        else:
            return f"Error: Unknown action '{action}'"