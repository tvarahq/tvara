"""
Hierarchical Workflow Demo

This example demonstrates a 3-level hierarchical workflow structure:
- Executive Manager (top level)
  - Content Supervisor (mid level) 
    - Weather Agent (leaf)
    - Poet Agent (leaf)
  - Communication Supervisor (mid level)
    - Gmail Agent (leaf)
    - Slack Agent (leaf)

This demo version works without requiring actual API keys for demonstration purposes.
"""

from tvara.core import Agent, Workflow, Prompt
import os

# Set demo API keys (replace with real keys for actual use)
os.environ['MODEL_API_KEY'] = os.getenv('MODEL_API_KEY', 'demo-key-for-testing')
os.environ['COMPOSIO_API_KEY'] = os.getenv('COMPOSIO_API_KEY', 'demo-key-for-testing')

def create_hierarchical_workflow_demo():
    """Create and return a hierarchical workflow for demonstration."""
    
    # Level 3: Leaf agents (workers)
    weather_agent = Agent(
        name="Weather Agent",
        model="gemini-2.5-flash",
        api_key=os.getenv("MODEL_API_KEY"),
        prompt=Prompt(
            raw_prompt="You are a weather expert. Provide accurate weather information for requested locations."
        )
    )

    poet_agent = Agent(
        name="Poet Agent",
        model="gemini-2.5-flash",
        api_key=os.getenv("MODEL_API_KEY"),
        prompt=Prompt(
            raw_prompt="You are a creative poet. Transform any information into beautiful, artistic poetry."
        )
    )

    gmail_agent = Agent(
        name="Gmail Agent",
        model="gemini-2.5-flash",
        api_key=os.getenv("MODEL_API_KEY"),
        prompt=Prompt(
            raw_prompt="You are an email expert. Handle all email-related tasks professionally."
        )
    )

    slack_agent = Agent(
        name="Slack Agent",
        model="gemini-2.5-flash",
        api_key=os.getenv("MODEL_API_KEY"),
        prompt=Prompt(
            raw_prompt="You are a Slack communication expert. Handle all Slack messaging tasks."
        )
    )

    # Level 2: Mid-level supervisors
    content_supervisor = Agent(
        name="Content Supervisor",
        model="gemini-2.5-flash",
        api_key=os.getenv("MODEL_API_KEY"),
        prompt=Prompt(
            raw_prompt="You are a content creation supervisor. Coordinate between data gathering and creative writing tasks. Delegate to weather agents for data and poets for creative content."
        ),
        sub_agents=[weather_agent, poet_agent]
    )

    communication_supervisor = Agent(
        name="Communication Supervisor", 
        model="gemini-2.5-flash",
        api_key=os.getenv("MODEL_API_KEY"),
        prompt=Prompt(
            raw_prompt="You are a communication supervisor. Handle all external communications through email and messaging platforms. Delegate to appropriate communication agents."
        ),
        sub_agents=[gmail_agent, slack_agent]
    )

    # Level 1: Top-level executive manager
    executive_manager = Agent(
        name="Executive Manager",
        model="gemini-2.5-flash",
        api_key=os.getenv("MODEL_API_KEY"),
        prompt=Prompt(
            raw_prompt="You are an executive manager coordinating multiple department supervisors. Analyze complex requests and delegate to the appropriate supervisors. You oversee Content and Communication departments."
        ),
        sub_agents=[content_supervisor, communication_supervisor]
    )

    # Create hierarchical workflow
    hierarchical_workflow = Workflow(
        name="Executive Weather Communication Workflow",
        agents=[],  # Empty for hierarchical mode
        mode="hierarchical",
        manager_agent=executive_manager,
        max_iterations=15
    )
    
    return hierarchical_workflow, executive_manager, content_supervisor, communication_supervisor

def print_hierarchy_visualization(executive_manager, content_supervisor, communication_supervisor):
    """Print a visual representation of the workflow hierarchy."""
    print(f"\n{'='*60}")
    print("WORKFLOW HIERARCHY STRUCTURE:")
    print(f"{'='*60}")
    print(f"└── {executive_manager.name}")
    print(f"    ├── {content_supervisor.name}")
    for agent in content_supervisor.sub_agents:
        symbol = "└──" if agent == content_supervisor.sub_agents[-1] else "├──"
        print(f"    │   {symbol} {agent.name}")
    print(f"    └── {communication_supervisor.name}")
    for agent in communication_supervisor.sub_agents:
        symbol = "└──" if agent == communication_supervisor.sub_agents[-1] else "├──"
        print(f"        {symbol} {agent.name}")
    
    print(f"\n{'='*60}")
    print("HIERARCHY STATISTICS:")
    print(f"{'='*60}")
    print(f"Total Levels: 3")
    print(f"Executive Managers: 1")
    print(f"Department Supervisors: {len(executive_manager.sub_agents)}")
    
    total_leaf_agents = sum(len(supervisor.sub_agents) for supervisor in executive_manager.sub_agents)
    print(f"Leaf Agents: {total_leaf_agents}")
    print(f"Total Agents in Hierarchy: {1 + len(executive_manager.sub_agents) + total_leaf_agents}")

def demonstrate_prompt_generation(workflow, executive_manager):
    """Demonstrate how hierarchical prompts are generated."""
    print(f"\n{'='*60}")
    print("HIERARCHICAL PROMPT DEMO:")
    print(f"{'='*60}")
    
    # Sample context for executive level
    context = {
        "original_input": "Get weather for SF, write a poem about it, email the poem to team@example.com",
        "completed_tasks": [],
        "current_supervisor": executive_manager,
        "hierarchy_path": ["Executive Manager"],
        "current_status": "starting"
    }
    
    prompt = workflow._create_hierarchical_manager_prompt(context)
    print("EXECUTIVE MANAGER PROMPT:")
    print("-" * 40)
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)

if __name__ == "__main__":
    print("🏗️ HIERARCHICAL WORKFLOW DEMONSTRATION")
    print("=" * 60)
    
    # Create the workflow
    workflow, executive_manager, content_supervisor, communication_supervisor = create_hierarchical_workflow_demo()
    
    # Print hierarchy visualization
    print_hierarchy_visualization(executive_manager, content_supervisor, communication_supervisor)
    
    # Demonstrate prompt generation
    demonstrate_prompt_generation(workflow, executive_manager)
    
    print(f"\n{'='*60}")
    print("✅ HIERARCHICAL WORKFLOW DEMO COMPLETE")
    print("=" * 60)
    print(f"The workflow is ready to execute with: workflow.run('your task here')")
    print(f"Current mode: {workflow.mode.value}")
    print(f"Manager agent: {workflow.manager_agent.name}")
    print(f"Max iterations: {workflow.max_iterations}")