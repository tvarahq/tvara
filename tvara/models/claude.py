import json
from typing import Awaitable, Callable

from anthropic import Anthropic, AsyncAnthropic

from .base import BaseModel


class ClaudeModel(BaseModel):
    def __init__(self, model_name: str, api_key: str):
        super().__init__()
        self.model_name = model_name
        self.client = Anthropic(api_key=api_key)
        # Async client reuses the same credentials for streaming support.
        self.async_client = AsyncAnthropic(api_key=api_key)

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
        anthropic_tools, system_content, anthropic_messages = (
            self._prepare_anthropic_request(messages, tools)
        )

        kwargs = dict(
            model=self.model_name,
            max_tokens=4096,
            messages=anthropic_messages,
        )
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools
        if system_content:
            kwargs["system"] = system_content

        response = self.client.messages.create(**kwargs)
        return self._parse_response(response)

    async def stream_response_with_tools(
        self,
        messages: list,
        tools: list,
        on_token: Callable[[str], Awaitable[None]],
    ) -> dict:
        """
        Stream text tokens via on_token, then return the assembled result dict.

        Uses AsyncAnthropic's messages.stream() context manager. Text deltas are
        forwarded to on_token as they arrive; tool_use blocks are collected from
        the final assembled message (Anthropic does not stream tool arguments).

        Returns:
            dict with keys:
              text: str | None
              tool_calls: list[{id, name, args}] | None
              usage: dict | None
        """
        anthropic_tools, system_content, anthropic_messages = (
            self._prepare_anthropic_request(messages, tools)
        )

        kwargs = dict(
            model=self.model_name,
            max_tokens=4096,
            messages=anthropic_messages,
        )
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools
        if system_content:
            kwargs["system"] = system_content

        async with self.async_client.messages.stream(**kwargs) as stream:
            async for event in stream:
                # event types: https://docs.anthropic.com/en/api/messages-streaming
                if (
                    event.type == "content_block_delta"
                    and hasattr(event, "delta")
                    and event.delta.type == "text_delta"
                ):
                    await on_token(event.delta.text)

            # get_final_message() blocks until the stream is fully consumed and
            # returns the complete Message object — identical to a non-streaming call.
            final_message = await stream.get_final_message()

        return self._parse_response(final_message)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _prepare_anthropic_request(
        self, messages: list, tools: list
    ) -> tuple:
        """Convert OpenAI-format messages/tools to Anthropic format.

        Returns:
            (anthropic_tools, system_content, anthropic_messages)
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

        return anthropic_tools, system_content, anthropic_messages

    def _parse_response(self, response) -> dict:
        """Normalise an Anthropic Message object into the shared dict schema."""
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
