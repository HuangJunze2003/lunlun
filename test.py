import asyncio
import os
from pathlib import Path

from agentscope.agent import ReActAgent
from agentscope.formatter import OpenAIChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel
from agentscope.tool import Toolkit, execute_python_code
from dotenv import load_dotenv


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


async def main() -> None:
    load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

    toolkit = Toolkit()
    toolkit.register_tool_function(execute_python_code)

    base_url = os.getenv("DASHSCOPE_BASE_URL")
    client_kwargs = {"base_url": base_url} if base_url else None

    jarvis = ReActAgent(
        name="Jarvis",
        sys_prompt="You're a helpful assistant named Jarvis.",
        model=OpenAIChatModel(
            model_name=os.getenv("DASHSCOPE_MODEL", "qwen3.5-plus"),
            api_key=require_env("DASHSCOPE_API_KEY"),
            stream=True,
            client_kwargs=client_kwargs,
            generate_kwargs={"temperature": 0},
        ),
        formatter=OpenAIChatFormatter(),
        toolkit=toolkit,
        memory=InMemoryMemory(),
    )

    msg = Msg(
        name="user",
        content="请调用 Python 工具并打印 Hello World。",
        role="user",
    )
    await jarvis(msg)


if __name__ == "__main__":
    asyncio.run(main())
