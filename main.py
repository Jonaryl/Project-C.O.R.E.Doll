import asyncio
import threading

from interface.main_interface import App
from interface.main_interface import MainTab
from core.agent import Agent

agent = Agent()
app = App(agent=agent)

# You should now have access to our previous message in this conversation. From my introduction. Tell me if you can't them.

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

# DONE : 

# add description to personality trait to try avoid default friendly response
# conversation == need run - event receiver independant
# state not take by prompt
# temporary memory / conversation history