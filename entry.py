# 这个文件没什么用，只是单纯用来测试模型是否运转正常
import asyncio
from agentscope.message import Msg
from agent_app.agent_factory import build_agent

async def main() -> None:
    agent = build_agent()
    await agent(Msg(name="user", content="你是谁？", role = "user"))
    
    
if __name__ == "__main__":
    asyncio.run(main())