from tvara.core import Agent
from tvara.tools import DateTool, WebSearchTool, CodeTool
from tvara.connectors import GitHubConnector, SlackConnector
from dotenv import load_dotenv
import os

load_dotenv()

my_slack_agent = Agent(
    name="Slack Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    tools=[WebSearchTool(api_key=os.getenv("TAVILY_API_KEY")), DateTool(), CodeTool()],
    connectors=[SlackConnector(name="slack", token=os.getenv("SLACK_BOT_TOKEN"))]
)

while True:
    user_input = input("User: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Exiting the agent.")
        break

    response = my_slack_agent.run(user_input)
    print(f"Agent: {response}")