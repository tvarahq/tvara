from tvara.core import Agent
from dotenv import load_dotenv
import os

load_dotenv()

agent = Agent(
    name="My Notion Agent",
    model="gemini-2.5-flash", 
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["notion"],
)

response = agent.run("hey hi there. can you summarize 'Ashish's 7th sem' page for me?")

print(response)