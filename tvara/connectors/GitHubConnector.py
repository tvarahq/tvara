import requests
from .base import BaseConnector
import json
from typing import Dict, Any, Union

class GitHubConnector(BaseConnector):
    def __init__(self, token: str):
        super().__init__(name="GitHub", token=token)
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def get_action_schema(self) -> dict:
        """
        Returns detailed schema with descriptions and examples to help LLM choose correctly.
        """
        return {
            "list_repos": {
                "description": "List all repositories for the authenticated user",
                "parameters": {},
                "example_use_case": "When user asks 'show me my repositories' or 'list my repos'"
            },
            "list_issues": {
                "description": "List all issues for a specific repository",
                "parameters": {
                    "owner": {"type": "string", "required": True, "description": "Repository owner username"},
                    "repo": {"type": "string", "required": True, "description": "Repository name"}
                },
                "example_use_case": "When user asks 'show issues in my-repo' or 'what are the open issues in owner/repo'"
            },
            "create_issue_comment": {
                "description": "Add a comment to an existing issue",
                "parameters": {
                    "owner": {"type": "string", "required": True, "description": "Repository owner username"},
                    "repo": {"type": "string", "required": True, "description": "Repository name"},
                    "issue_number": {"type": "integer", "required": True, "description": "Issue number (not ID)"},
                    "comment": {"type": "string", "required": True, "description": "Comment text to add"}
                },
                "example_use_case": "When user asks 'comment on issue #5' or 'add comment to issue'"
            },
            "get_repo_info": {
                "description": "Get detailed information about a repository",
                "parameters": {
                    "owner": {"type": "string", "required": True, "description": "Repository owner username"},
                    "repo": {"type": "string", "required": True, "description": "Repository name"}
                },
                "example_use_case": "When user asks 'tell me about this repo' or 'get repo details'"
            },
            "get_repo_contents": {
                "description": "Get the contents of a file or directory in a repository",
                "parameters": {
                    "owner": {"type": "string", "required": True, "description": "Repository owner username"},
                    "repo": {"type": "string", "required": True, "description": "Repository name"},
                    "path": {"type": "string", "required": False, "description": "File or directory path (empty for root)"}
                },
                "example_use_case": "When user asks 'show me the README' or 'get contents of src/main.py'"
            }
        }

    def _handle_response(self, response: requests.Response, action: str) -> Union[Dict[Any, Any], str]:
        """
        Standardized response handling with better error messages.
        """
        try:
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return f"Error: Resource not found (404). Please check if the repository/issue exists and you have access."
            elif response.status_code == 401:
                return f"Error: Authentication failed (401). Please check your GitHub token."
            elif response.status_code == 403:
                return f"Error: Access forbidden (403). You may not have permission or hit rate limits."
            else:
                return f"Error: HTTP {response.status_code} - {response.text}"
        except json.JSONDecodeError:
            return f"Error: Invalid JSON response from GitHub API"
        except Exception as e:
            return f"Error processing response: {str(e)}"

    def run(self, action: str, input: dict) -> Union[Dict[Any, Any], str]:
        """
        Enhanced run method with better validation and error handling.
        """
        try:
            if action == "list_repos":
                response = requests.get(
                    f"{self.base_url}/user/repos",
                    headers=self.headers,
                    params={"sort": "updated", "per_page": 30}
                )
                return self._handle_response(response, action)

            elif action == "list_issues":
                owner = input.get("owner")
                repo = input.get("repo")
                
                if not owner or not repo:
                    return {
                        "error": "Missing required parameters",
                        "message": "'owner' and 'repo' are required for 'list_issues' action.",
                        "required_params": ["owner", "repo"]
                    }
                
                response = requests.get(
                    f"{self.base_url}/repos/{owner}/{repo}/issues",
                    headers=self.headers,
                    params={"state": "open", "per_page": 30}
                )
                return self._handle_response(response, action)

            elif action == "create_issue_comment":
                owner = input.get("owner")
                repo = input.get("repo")
                issue_number = input.get("issue_number")
                comment = input.get("comment")
                
                missing_params = []
                if not owner: missing_params.append("owner")
                if not repo: missing_params.append("repo")
                if issue_number is None: missing_params.append("issue_number")
                if not comment: missing_params.append("comment")
                
                if missing_params:
                    return {
                        "error": "Missing required parameters",
                        "message": f"The following parameters are required: {', '.join(missing_params)}",
                        "missing_params": missing_params
                    }
                
                data = {"body": comment}
                response = requests.post(
                    f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments",
                    json=data,
                    headers=self.headers
                )
                return self._handle_response(response, action)
            
            elif action == "get_repo_info":
                owner = input.get("owner")
                repo = input.get("repo")
                
                if not owner or not repo:
                    return {
                        "error": "Missing required parameters",
                        "message": "'owner' and 'repo' are required for 'get_repo_info' action.",
                        "required_params": ["owner", "repo"]
                    }

                response = requests.get(
                    f"{self.base_url}/repos/{owner}/{repo}",
                    headers=self.headers
                )
                return self._handle_response(response, action)
            
            elif action == "get_repo_contents":
                owner = input.get("owner")
                repo = input.get("repo")
                path = input.get("path", "")
                
                if not owner or not repo:
                    return {
                        "error": "Missing required parameters",
                        "message": "'owner' and 'repo' are required for 'get_repo_contents' action.",
                        "required_params": ["owner", "repo"]
                    }

                api_url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
                response = requests.get(api_url, headers=self.headers)
                
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{path}"
                raw_response = requests.get(raw_url)
                
                if raw_response.status_code == 200:
                    return {
                        "type": "file",
                        "content": raw_response.text,
                        "path": path,
                        "source": "raw"
                    }

            else:
                return {
                    "error": "Unknown action",
                    "message": f"Action '{action}' is not supported.",
                    "available_actions": list(self.get_action_schema().keys())
                }
                
        except requests.RequestException as e:
            return f"Network error: {str(e)}"
        except Exception as e:
            return f"Unexpected error in action '{action}': {str(e)}"
