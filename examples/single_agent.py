from tvara.core import Agent
from tvara.tools import DateTool, WebSearchTool, CodeTool
from tvara.connectors import GitHubConnector
from dotenv import load_dotenv
import os

load_dotenv()

basic_agent = Agent(
    name="SadAI",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    tools=[WebSearchTool(api_key=os.getenv("TAVILY_API_KEY")), DateTool(), CodeTool()],
    connectors=[GitHubConnector(name="github", token=os.getenv("GITHUB_PAT"))]
)

print(basic_agent.run("hey write a code to list out all files in my directory"))

# while True:
#     user_input = input("User: ")
#     if user_input.lower() in ["exit", "quit"]:
#         print("Exiting the agent.")
#         break

#     response = basic_agent.run(user_input)
#     print(f"Agent: {response}")