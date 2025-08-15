from tvara.core import Agent, Workflow, Prompt
from dotenv import load_dotenv
import os

load_dotenv()

blue = "\033[94m"
reset = "\033[0m"

basic_agent = Agent(
    name="GitHub Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    tools=[WebSearchTool(api_key=os.getenv("TAVILY_API_KEY")), DateTool(), CodeTool()],
    connectors=[GitHubConnector(token=os.getenv("GITHUB_PAT"))]
)

summarizer_agent = Agent(
    name="Summarizer",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
)

slack_agent = Agent(
    name="Slack Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    connectors=[SlackConnector(token=os.getenv("SLACK_BOT_TOKEN"))]
)

manager_agent = Agent(
    name="Manager Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    prompt=Prompt(
        raw_prompt="You are a workflow manager coordinating multiple AI agents. Your job is to decide what should happen next."
    )
)

my_workflow = Workflow(
    name= "Sample Workflow",
    agents=[basic_agent, summarizer_agent, slack_agent],
    mode= "supervised",
    manager_agent=manager_agent,
)