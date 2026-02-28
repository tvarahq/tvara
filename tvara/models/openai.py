import json
from .base import BaseModel
from openai import OpenAI

class OpenAIModel(BaseModel):
    def __init__(self, model_name: str, api_key: str):
        super().__init__()
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key)

    def get_response(self, input_data: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": input_data}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def get_response_with_tools(self, messages: list, tools: list) -> dict:
        """
        Call the model with native function calling.

        Returns:
            dict with keys:
              text: str | None  (set when model gives a final text answer)
              tool_calls: list[{id, name, args}] | None  (set when model invokes tools)
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        message = response.choices[0].message

        if message.tool_calls:
            return {
                "text": None,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "args": json.loads(tc.function.arguments),
                    }
                    for tc in message.tool_calls
                ],
            }
        return {"text": message.content, "tool_calls": None}
