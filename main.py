import asyncio
from interface.main_interface import App
from core.agent import Agent
from core.message_bus import MessageBus

agent = Agent()
app = App(agent=agent)

async def main():
    await agent.main()
    app.mainloop()


if __name__ == "__main__":
    asyncio.run(main())