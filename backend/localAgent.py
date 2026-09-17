"""
Copyright (c) 2023-2026 钧朔 - JunSu - AI
Released under the MIT License.
See LICENSE file for full license text.
"""

# This is only call Ollama locally for testing pupose
# pip install -qU langchain langchain-ollama

from langchain.agents import create_agent


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


test_agent = create_agent(
    model="ollama:qwen2.5:7b",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

result = test_agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather in DAlain China?"}]}
)
print(result["messages"][-1].content_blocks)
