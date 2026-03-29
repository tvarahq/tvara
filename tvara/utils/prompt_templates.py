def agent_prompt_template(**kwargs) -> str:
    tools = kwargs.get("tools", [])

    if tools:
        tools_section = "Available tools:\n" + "\n".join(
            f"- {tool.name}: {tool.description}" for tool in tools
        )
    else:
        tools_section = "No tools available."

    return f"""You are an AI assistant that can use tools to help answer questions.
{tools_section}
"""

template_registry = {
    "agent_prompt_template": agent_prompt_template,
}
