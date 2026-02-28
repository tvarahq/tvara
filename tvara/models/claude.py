import json
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
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": input_data}
                ]
            )
            return message.content[0].text
        except Exception as e:
            return f"Error: {str(e)}"

    def get_response_with_tools(self, messages: list, tools: list) -> dict:
        """
        Call Claude with native tool use.

        Converts OpenAI-format messages and tools to Anthropic format, then
        normalises the response back to the shared dict schema.

        Returns:
            dict with keys:
              text: str | None
              tool_calls: list[{id, name, args}] | None
              usage: dict | None
        """
        # --- Convert OpenAI tool schema → Anthropic tool schema ---
        anthropic_tools = []
        for t in tools:
            fn = t["function"]
            anthropic_tools.append({
                "name": fn["name"],
                "description": fn.get("description", ""),
                "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
            })

        # --- Split system message from the conversation ---
        system_content = ""
        conversation = []
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"] or ""
            else:
                conversation.append(msg)

        # Anthropic requires at least one user message
        if not conversation:
            conversation = [{"role": "user", "content": "Hello"}]

        # --- Rebuild conversation in Anthropic format ---
        # Tool-result messages need special handling
        anthropic_messages = []
        for msg in conversation:
            role = msg["role"]
            if role == "tool":
                # Anthropic expects tool results as part of a user message
                anthropic_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg["tool_call_id"],
                            "content": msg["content"],
                        }
                    ],
                })
            elif role == "assistant" and msg.get("tool_calls"):
                # Convert OpenAI assistant tool-call turn → Anthropic format
                content = []
                if msg.get("content"):
                    content.append({"type": "text", "text": msg["content"]})
                for tc in msg["tool_calls"]:
                    args = tc["function"]["arguments"]
                    content.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "input": json.loads(args) if isinstance(args, str) else args,
                    })
                anthropic_messages.append({"role": "assistant", "content": content})
            else:
                anthropic_messages.append({"role": role, "content": msg.get("content") or ""})

        kwargs = dict(
            model=self.model_name,
            max_tokens=4096,
            tools=anthropic_tools,
            messages=anthropic_messages,
        )
        if system_content:
            kwargs["system"] = system_content

        response = self.client.messages.create(**kwargs)

        usage = None
        if hasattr(response, "usage"):
            usage = {
                "input_tokens": getattr(response.usage, "input_tokens", None),
                "output_tokens": getattr(response.usage, "output_tokens", None),
            }

        if response.stop_reason == "tool_use":
            tool_calls = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "args": block.input,
                    })
            return {"text": None, "tool_calls": tool_calls, "usage": usage}

        # Final text response
        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text += block.text
        return {"text": text, "tool_calls": None, "usage": usage}
