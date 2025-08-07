from tvara.core import Agent, Prompt, Workflow
from tvara.tools import WebSearchTool

MODEL_API_KEY="AIzaSyCaETU_k9jariRsRb38e4n37gF0FTjrBSY"
TAVILY_API_KEY="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"

my_agent = Agent(
    name="Sample Agent",
    model="gemini-2.5-flash",
    api_key=MODEL_API_KEY,
    prompt=Prompt(raw_prompt="")
)

history = {
    "user": [],
    "agent": []
}

while True:
    user_input = input("User: ")

    if user_input == 'exit':
        break

    history.get('user').append(user_input)

    response = my_agent.run(str(history) + user_input)

    history.get('agent').append(response)

    print(response)