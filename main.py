import asyncio
import threading

from interface.main_interface import App
from interface.main_interface import MainTab
from core.agent import Agent

agent = Agent()
app = App(agent=agent)

# Hello, i'm Jonaryl, the developpeur of your cognitive systems

def start_asyncio_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

async def agent_startup():
    await agent.main()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    
    t = threading.Thread(target=start_asyncio_loop, args=(loop,), daemon=True)
    t.start()
    
    asyncio.run_coroutine_threadsafe(agent_startup(), loop)
    
    app.mainloop()



# NEXT : 

# conversation == need run
# temporary memory / conversation history

# base memory



# DONE : 
