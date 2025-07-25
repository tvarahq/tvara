from typing import List, Optional

def base_prompt(desc: str, tools: Optional[List[str]] = None) -> str:
    """
    Generates a base prompt for the agent.
    
    Args:
        desc (str): A description of the agent's capabilities.
        tools (list): A list of tools available to the agent.

    Returns:
        str: The base prompt containing the agent's description and tools.
    """
    prompt = f"""
    You are a smart AI agent designed to assist with various tasks.
    The following tools are at your disposal: {', '.join(tools) if tools else 'None'}.
    Your role as an AI agent is to perform the following task as described by the user:
    {desc}.
    Please provide a detailed response based on the tools and your understanding of the problem.
    """
    return prompt