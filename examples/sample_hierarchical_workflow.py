from tvara.core import Agent, Workflow, Prompt
from dotenv import load_dotenv
import os

load_dotenv()

# Create leaf agents (workers)
weather_agent = Agent(
    name="Weather Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["WEATHERMAP"],
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
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["gmail"],
    prompt=Prompt(
        raw_prompt="You are an email expert. Handle all email-related tasks professionally."
    )
)

slack_agent = Agent(
    name="Slack Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["slack"],
    prompt=Prompt(
        raw_prompt="You are a Slack communication expert. Handle all Slack messaging tasks."
    )
)

# Create mid-level supervisors
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

# Create top-level manager
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

# Test the workflow
if __name__ == "__main__":
    result = hierarchical_workflow.run(
        "Get the current weather for San Francisco, create a poetic description of it, and send both the weather data and poem to team@tvarahq.com via email, then also share a summary in the #general Slack channel"
    )
    
    print(f"\n{'='*60}")
    print(f"FINAL RESULT: {result.final_output}")
    print(f"SUCCESS: {result.success}")
    print(f"AGENT OUTPUTS: {len(result.agent_outputs)} total steps")
    
    # Print hierarchy visualization
    print(f"\n{'='*60}")
    print("WORKFLOW HIERARCHY:")
    print(f"└── {executive_manager.name}")
    print(f"    ├── {content_supervisor.name}")
    print(f"    │   ├── {weather_agent.name}")
    print(f"    │   └── {poet_agent.name}")
    print(f"    └── {communication_supervisor.name}")
    print(f"        ├── {gmail_agent.name}")
    print(f"        └── {slack_agent.name}")