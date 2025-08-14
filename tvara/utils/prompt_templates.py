import json

def basic_prompt_template(**kwargs) -> str:
    tools_str = ", ".join([t.name for t in kwargs.get("tools", [])]) if kwargs.get("tools") else "no tools"
    conns_str = ", ".join([c.name for c in kwargs.get("connectors", [])]) if kwargs.get("connectors") else "no connectors"

    connector_docs = ""
    for conn in kwargs.get("connectors", []):
        if hasattr(conn, "get_action_schema"):
            connector_docs += f"\nConnector: {conn.name}\n"
            for action, schema in conn.get_action_schema().items():
                connector_docs += f"- Action: {action}\n  Input schema: {json.dumps(schema)}\n"

    return f"""
You are an AI assistant who is helpful and friendly.

You have access to the following tools:
{tools_str}

You are integrated with the following systems:
{conns_str}

Here are the supported connector actions and their expected inputs:
{connector_docs or "No connector actions registered."}

Your primary role is to assist the user by intelligently deciding whether to use a tool or a connector, or respond directly.

### VERY IMPORTANT ###

If a tool is available and relevant to the user's request, respond ONLY with this JSON:
{{
  "tool_call": {{
    "tool_name": "<tool_name>",
    "tool_input": "<tool_input>"
  }}
}}

If a connector is more suitable, respond ONLY with this JSON:
{{
  "connector_call": {{
    "connector_name": "<connector_name>",
    "connector_action": "<action>",
    "connector_input": {{
      "<key>": "<value>",
      ...
    }}
  }}
}}

Do NOT explain your actions. Do NOT include natural language.
When using `code_tool`, always return actual executable Python code.

Only if no tool or connector is relevant should you answer in natural language.
"""

def agent_prompt_template(**kwargs) -> str:
  tools = kwargs.get("tools", [])
    
  if tools:
    tools_list = "\n".join([f"- {tool.name}: {tool.description}" for tool in tools])
    tools_section = f"""
        Available tools:
        {tools_list}
        """
  else:
    tools_section = "No tools available."
              
  return f"""You are an AI assistant that can use tools to help answer questions.
    {tools_section}
    Instructions:
    Analyze the user's request carefully
    If you need to use a tool, respond with JSON in this format: {{"tool_call": {{"tool_name": "tool_name", "tool_input": "input_data"}}}}
    If you have enough information to answer, provide a direct response
    You can use multiple tools in sequence - after each tool result, decide if you need more information
      For GitHub-related queries, use tools like:
      github_get_user_repos: to get user repositories
      github_search_repositories: to search for repositories
      github_get_repository: to get specific repository details
      Current conversation context will be provided below.
  """


template_registry = {
    "basic_prompt_template": basic_prompt_template,
    "agent_prompt_template": agent_prompt_template,
}
