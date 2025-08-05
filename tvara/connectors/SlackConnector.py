import requests
from .base import BaseConnector
import json
from typing import Dict, Any, Union

class SlackConnector(BaseConnector):
    def __init__(self, token: str):
        super().__init__(name="Slack", token=token)
        self.base_url = "https://slack.com/api"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self._channel_cache = {} 

    def get_action_schema(self) -> dict:
        """
        Returns detailed schema with descriptions and examples to help LLM choose correctly.
        """
        return {
            "list_channels": {
                "description": "List all channels in the workspace that the user has access to",
                "parameters": {
                    "types": {"type": "string", "required": False, "description": "Channel types (public_channel,private_channel,mpim,im)"},
                    "limit": {"type": "integer", "required": False, "description": "Max channels to return (default: 100)"}
                },
                "example_use_case": "When user asks 'show me all channels' or 'list workspace channels'"
            },
            "send_message": {
                "description": "Send a message to a channel or user as the authenticated user",
                "parameters": {
                    "channel": {"type": "string", "required": True, "description": "Channel ID or name (#general, @username, or channel ID)"},
                    "text": {"type": "string", "required": True, "description": "Message text to send"},
                    "thread_ts": {"type": "string", "required": False, "description": "Reply in thread timestamp"}
                },
                "example_use_case": "When user asks 'send message to #general' or 'post hello in channel'"
            },
            "get_channel_history": {
                "description": "Get recent messages from a channel",
                "parameters": {
                    "channel": {"type": "string", "required": True, "description": "Channel ID or name"},
                    "limit": {"type": "integer", "required": False, "description": "Number of messages (default: 10)"}
                },
                "example_use_case": "When user asks 'show recent messages from #general' or 'get channel history'"
            },
            "get_user_info": {
                "description": "Get information about a user",
                "parameters": {
                    "user": {"type": "string", "required": True, "description": "User ID or username"}
                },
                "example_use_case": "When user asks 'tell me about @john' or 'get user details'"
            },
            "search_messages": {
                "description": "Search for messages in the workspace",
                "parameters": {
                    "query": {"type": "string", "required": True, "description": "Search query"},
                    "count": {"type": "integer", "required": False, "description": "Number of results (default: 20)"}
                },
                "example_use_case": "When user asks 'search for messages about project' or 'find keyword'"
            },
            "get_workspace_info": {
                "description": "Get information about the current workspace",
                "parameters": {},
                "example_use_case": "When user asks 'tell me about this workspace' or 'workspace details'"
            },
            "upload_file": {
                "description": "Upload a file to Slack",
                "parameters": {
                    "channels": {"type": "string", "required": True, "description": "Channel ID or name"},
                    "content": {"type": "string", "required": True, "description": "File content as text"},
                    "filename": {"type": "string", "required": True, "description": "Name of the file"},
                    "title": {"type": "string", "required": False, "description": "File title"}
                },
                "example_use_case": "When user asks 'upload file to #general' or 'share document'"
            },
            "get_my_profile": {
                "description": "Get the authenticated user's profile information",
                "parameters": {},
                "example_use_case": "When user asks 'show my profile' or 'what's my status'"
            }
        }

    def _handle_response(self, response: requests.Response, action: str) -> Union[Dict[Any, Any], str]:
        """
        Standardized response handling with better error messages.
        """
        try:
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return data
                else:
                    error = data.get("error", "Unknown error")
                    return f"Slack API Error: {error}"
            elif response.status_code == 401:
                return f"Error: Authentication failed (401). Please check your Slack user token."
            elif response.status_code == 403:
                return f"Error: Access forbidden (403). User token may not have required permissions."
            elif response.status_code == 429:
                return f"Error: Rate limit exceeded (429). Please try again later."
            else:
                return f"Error: HTTP {response.status_code} - {response.text}"
        except json.JSONDecodeError:
            return f"Error: Invalid JSON response from Slack API"
        except Exception as e:
            return f"Error processing response: {str(e)}"

    def _resolve_channel_id(self, channel: str) -> str:
        """Helper to resolve channel name to ID if needed."""
        if channel.startswith('#'):
            channel = channel[1:]
        return channel

    def _resolve_user_id(self, user: str) -> str:
        """Helper to resolve username to user ID if needed."""
        if user.startswith('@'):
            user = user[1:]
        return user
    
    def _get_channel_id(self, channel_name: str) -> str:
        if channel_name.startswith('#'):
            channel_name = channel_name[1:]
        
        if channel_name in self._channel_cache:
            return self._channel_cache[channel_name]
        
        if channel_name.startswith('C') and len(channel_name) > 8:
            return channel_name
        
        try:
            response = requests.get(
                f"{self.base_url}/conversations.list",
                headers=self.headers,
                params={"types": "public_channel,private_channel", "limit": 1000}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    for channel in data.get("channels", []):
                        name = channel.get("name")
                        channel_id = channel.get("id")
                        if name and channel_id:
                            self._channel_cache[name] = channel_id
                            if name == channel_name:
                                return channel_id
        except Exception:
            pass
        
        return channel_name

    def run(self, action: str, input: dict) -> Union[Dict[Any, Any], str]:
        """
        Enhanced run method with better validation and error handling.
        """
        try:
            if action == "list_channels":
                types = input.get("types", "public_channel,private_channel")
                limit = input.get("limit", 100)
                response = requests.get(
                    f"{self.base_url}/conversations.list",
                    headers=self.headers,
                    params={"types": types, "limit": limit}
                )
                return self._handle_response(response, action)

            elif action == "send_message":
                channel = input.get("channel")
                text = input.get("text")
                
                if not channel or not text:
                    
                    return {
                        "error": "Missing required parameters",
                        "message": "'channel' and 'text' are required for 'send_message' action.",
                        "required_params": ["channel", "text"]
                    }
                
                channel_id = self._get_channel_id(channel)
                
                response = requests.post(
                    f"{self.base_url}/chat.postMessage",
                    headers=self.headers,
                    json={"channel": channel_id, "text": text}
                )
                return self._handle_response(response, action)

            elif action == "get_channel_history":
                channel = input.get("channel")
                limit = input.get("limit", 10)
                
                if not channel:
                    return {
                        "error": "Missing required parameters",
                        "message": "'channel' is required for 'get_channel_history' action.",
                        "required_params": ["channel"]
                    }
                
                channel_id = self._get_channel_id(channel)
                
                response = requests.get(
                    f"{self.base_url}/conversations.history",
                    headers=self.headers,
                    params={"channel": channel_id, "limit": limit}
                )
                return self._handle_response(response, action)

            elif action == "get_user_info":
                user = input.get("user")
                
                if not user:
                    return {
                        "error": "Missing required parameters",
                        "message": "'user' is required for 'get_user_info' action.",
                        "required_params": ["user"]
                    }
                
                user = self._resolve_user_id(user)
                response = requests.get(
                    f"{self.base_url}/users.info",
                    headers=self.headers,
                    params={"user": user}
                )
                return self._handle_response(response, action)

            elif action == "search_messages":
                query = input.get("query")
                count = input.get("count", 20)
                
                if not query:
                    return {
                        "error": "Missing required parameters",
                        "message": "'query' is required for 'search_messages' action.",
                        "required_params": ["query"]
                    }
                
                response = requests.get(
                    f"{self.base_url}/search.messages",
                    headers=self.headers,
                    params={"query": query, "count": count}
                )
                return self._handle_response(response, action)

            elif action == "get_workspace_info":
                response = requests.get(
                    f"{self.base_url}/team.info",
                    headers=self.headers
                )
                return self._handle_response(response, action)

            elif action == "upload_file":
                channels = input.get("channels")
                content = input.get("content")
                filename = input.get("filename")
                title = input.get("title", filename)
                
                missing_params = []
                if not channels: missing_params.append("channels")
                if not content: missing_params.append("content")
                if not filename: missing_params.append("filename")
                
                if missing_params:
                    return {
                        "error": "Missing required parameters",
                        "message": f"Required parameters: {', '.join(missing_params)}",
                        "missing_params": missing_params
                    }
                
                channels = self._resolve_channel_id(channels)
                response = requests.post(
                    f"{self.base_url}/files.upload",
                    headers=self.headers,
                    json={
                        "channels": channels,
                        "content": content,
                        "filename": filename,
                        "title": title
                    }
                )
                return self._handle_response(response, action)

            elif action == "get_my_profile":
                response = requests.get(
                    f"{self.base_url}/users.profile.get",
                    headers=self.headers
                )
                return self._handle_response(response, action)

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
