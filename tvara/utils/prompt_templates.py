import json

def basic_prompt_template(name: str, description: str, **kwargs) -> str:
    tools_str = ", ".join([t.name for t in kwargs.get("tools", [])]) if kwargs.get("tools") else "no tools"
    conns_str = ", ".join([c.name for c in kwargs.get("connectors", [])]) if kwargs.get("connectors") else "no connectors"

    connector_docs = ""
    for conn in kwargs.get("connectors", []):
        if hasattr(conn, "get_action_schema"):
            connector_docs += f"\nConnector: {conn.name}\n"
            for action, schema in conn.get_action_schema().items():
                connector_docs += f"- Action: {action}\n  Input schema: {json.dumps(schema)}\n"

    return f"""
You are {name}, {description}

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


template_registry = {
    "basic_prompt_template": basic_prompt_template,
}
