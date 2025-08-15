from tvara.core import Agent
from dotenv import load_dotenv
import os

load_dotenv()

try:
    from composio import Composio
    composio_client = Composio(api_key=os.getenv("COMPOSIO_API_KEY"))
    print("Composio client initialized successfully")
except Exception as e:
    print(f"Composio initialization failed: {e}")

agent = Agent(
    name="GitHub-Slack Agent",
    model="gemini-2.5-flash", 
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["COMPOSIO_SEARCH"]
)

response = agent.run("hey hi there. latest news on india pakistan")
print(response)
