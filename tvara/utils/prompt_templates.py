from typing import List

def basic_prompt_template(name: str, description: str, **kwargs) -> str:
    return f"You are {name}. {description}"

def tool_aware_template(name: str, description: str, tools: List[str], **kwargs) -> str:
    tool_list = ", ".join(tools) if tools else "no tools"
    return f"You are {name}. {description} You have access to tools: {tool_list}."

def connector_aware_template(name: str, description: str, connectors: List[str], **kwargs) -> str:
    connector_list = ", ".join(connectors) if connectors else "no connectors"
    return f"You are {name}. {description} You are connected to: {connector_list}."

def fully_aware_template(name: str, description: str, tools: List[str], connectors: List[str], **kwargs) -> str:
    tools_str = ", ".join(tools) if tools else "no tools"
    conns_str = ", ".join(connectors) if connectors else "no connectors"
    return f"""You are {name}. {description}
You can use the following tools: {tools_str}.
You are integrated with: {conns_str}."""

template_registry = {
    "basic_prompt_template": basic_prompt_template,
    "tool_aware_template": tool_aware_template,
    "connector_aware_template": connector_aware_template,
    "fully_aware_template": fully_aware_template,
}
