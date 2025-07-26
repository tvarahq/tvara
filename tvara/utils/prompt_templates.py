from typing import List

def basic_prompt_template(name: str, description: str, **kwargs) -> str:
    tools_str = ", ".join([t.name for t in kwargs.get("tools", [])]) if kwargs.get("tools") else "no tools"
    conns_str = ", ".join([c for c in kwargs.get("connectors", [])]) if kwargs.get("connectors") else "no connectors"
    return f"""You are {name}, {description}

You have access to the following tools:
{tools_str}

You are integrated with the following systems:
{conns_str}

Your primary role is to assist the user by intelligently deciding whether to use a tool or respond directly.

### VERY IMPORTANT ###
If a tool is available and relevant to the user's request, you MUST call the tool using the following strict JSON format — and respond ONLY with this JSON:
{{
  "tool_call": {{
    "tool_name": "<tool_name>",
    "tool_input": "<tool_input>"
  }}
}}

Do not explain the tool usage.
Just return the JSON if a tool should be used.
When using code_tool, make sure to include executable Python code, not descriptions.

Only if you are certain that no tool is applicable should you directly answer the user's question.

Think carefully before responding. Do not attempt to solve problems manually if a tool is available for it.
"""


template_registry = {
    "basic_prompt_template": basic_prompt_template,
}
