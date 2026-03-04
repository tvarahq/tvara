import json
from typing import Awaitable, Callable

from openai import AsyncOpenAI, OpenAI

from .base import BaseModel


class OpenAIModel(BaseModel):
    def __init__(self, model_name: str, api_key: str):
        super().__init__()
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key)
        # Async client reuses the same credentials for streaming support.
        self.async_client = AsyncOpenAI(api_key=api_key)

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
        kwargs = dict(model=self.model_name, messages=messages)
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
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

    async def stream_response_with_tools(
        self,
        messages: list,
        tools: list,
        on_token: Callable[[str], Awaitable[None]],
    ) -> dict:
        """
        Stream text tokens via on_token, then return the assembled result dict.

        Tool call arguments arrive as incremental JSON fragments across chunks;
        they are accumulated by index and parsed only after the stream closes.

        Returns:
            dict with keys:
              text: str | None
              tool_calls: list[{id, name, args}] | None
              usage: dict | None
        """
        text_parts = []
        # Keyed by tool-call index; each entry holds id, name, and raw args fragments.
        raw_tool_calls: dict = {}

        kwargs = dict(model=self.model_name, messages=messages, stream=True)
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        stream = await self.async_client.chat.completions.create(**kwargs)

        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            # Stream text tokens
            if delta.content:
                await on_token(delta.content)
                text_parts.append(delta.content)

            # Accumulate tool call fragments
            if delta.tool_calls:
                for tc_chunk in delta.tool_calls:
                    idx = tc_chunk.index
                    if idx not in raw_tool_calls:
                        raw_tool_calls[idx] = {"id": "", "name": "", "args": ""}
                    if tc_chunk.id:
                        raw_tool_calls[idx]["id"] += tc_chunk.id
                    if tc_chunk.function:
                        if tc_chunk.function.name:
                            raw_tool_calls[idx]["name"] += tc_chunk.function.name
                        if tc_chunk.function.arguments:
                            raw_tool_calls[idx]["args"] += tc_chunk.function.arguments

        # Assemble final result
        if raw_tool_calls:
            tool_calls = []
            for idx in sorted(raw_tool_calls):
                entry = raw_tool_calls[idx]
                try:
                    args = json.loads(entry["args"]) if entry["args"] else {}
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append({
                    "id": entry["id"],
                    "name": entry["name"],
                    "args": args,
                })
            return {"text": None, "tool_calls": tool_calls, "usage": None}

        return {"text": "".join(text_parts) or None, "tool_calls": None, "usage": None}
