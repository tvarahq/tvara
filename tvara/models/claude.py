from .base import BaseModel
from anthropic import Anthropic

class ClaudeModel(BaseModel):
    def __init__(self, model_name: str, api_key: str):
        super().__init__()
        self.model_name = model_name
        self.client = Anthropic(api_key=api_key)

    def get_response(self, input_data: str) -> str:
        """
        Gets a response from the Claude model.

        Args:
            input_data (str): The user's input.

        Returns:
            str: The generated response from Claude.
        """
        try:
            message = self.client.messages.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": input_data}
                ]
            )
            return message.content
        except Exception as e:
            return f"Error: {str(e)}"
