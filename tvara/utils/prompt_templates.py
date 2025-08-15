import json

def basic_prompt_template(**kwargs) -> str:
    tools = kwargs.get("tools", [])
    
    if tools:
        tools_info = []
        for tool in tools:
            params_schema = tool.get_parameters_schema() if hasattr(tool, 'get_parameters_schema') else {}
            tool_info = f"""
Tool: {tool.name}
Description: {tool.description}
Parameters Schema: {json.dumps(params_schema, indent=2) if params_schema else 'No specific parameters required'}
"""
            tools_info.append(tool_info)
        tools_str = "\n".join(tools_info)
    else:
        tools_str = "No tools available"
    
    conns_str = ", ".join([c.name for c in kwargs.get("connectors", [])]) if kwargs.get("connectors") else "no connectors"

    connector_docs = ""
    for conn in kwargs.get("connectors", []):
        if hasattr(conn, "get_action_schema"):
            connector_docs += f"\nConnector: {conn.name}\n"
            for action, schema in conn.get_action_schema().items():
                connector_docs += f"- Action: {action}\n  Input schema: {json.dumps(schema)}\n"

    return f"""
You are an AI assistant who is helpful and friendly.

You have access to the following tools with their parameter schemas:
{tools_str}

You are integrated with the following systems:
{conns_str}

Here are the supported connector actions and their expected inputs:
{connector_docs or "No connector actions registered."}

Your primary role is to assist the user by intelligently deciding whether to use a tool or a connector, or respond directly.

### VERY IMPORTANT ###

When using tools, you MUST use the exact parameter names and structure as specified in the Parameters Schema.

If a tool is available and relevant to the user's request, respond ONLY with this JSON:
{{
  "tool_call": {{
    "tool_name": "<exact_tool_name>",
    "tool_input": {{
      // Use the exact parameter names and types from the tool's parameters schema
    }}
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
        tools_info = []
        for tool in tools:
            params_schema = tool.get_parameters_schema() if hasattr(tool, 'get_parameters_schema') else {}
            tool_info = f"""
- {tool.name}: {tool.description}
  Parameters Schema: {json.dumps(params_schema, indent=2) if params_schema else 'No specific parameters required'}"""
            tools_info.append(tool_info)
        tools_section = f"""
Available tools:
{"".join(tools_info)}
"""
    else:
        tools_section = "No tools available."
              
    return f"""You are an AI assistant that can use tools to help answer questions.
{tools_section}

Instructions:
1. Analyze the user's request carefully
2. If you need to use a tool, respond with JSON in this EXACT format: 
   {{"tool_call": {{"tool_name": "exact_tool_name", "tool_input": {{"param1": "value1", "param2": "value2"}}}}}}
3. IMPORTANT: Use the exact parameter names and structure as specified in each tool's Parameters Schema
4. If you have enough information to answer, provide a direct response
5. You can use multiple tools in sequence - after each tool result, decide if you need more information
6. Current conversation context will be provided below

In case a tool call fails, state clearly 'tool failed' or 'error executing tool'.

Example of correct tool usage:
If a tool has parameters schema: {{"type": "object", "properties": {{"email": {{"type": "string"}}, "subject": {{"type": "string"}}}}}}
Then use: {{"tool_call": {{"tool_name": "tool_name", "tool_input": {{"email": "user@example.com", "subject": "Hello"}}}}}}
"""

template_registry = {
    "basic_prompt_template": basic_prompt_template,
    "agent_prompt_template": agent_prompt_template,
}