from langchain.agents import create_agent
from langchain.agents.middleware import LLMToolEmulator

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="qwen3-max",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
    middleware=[LLMToolEmulator(tools=["get_weather"])],
)

# Run the agent
agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)