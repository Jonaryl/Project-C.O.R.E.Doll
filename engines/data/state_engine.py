import asyncio
from tools.file_r import FileRead
from tools.file_w import FileWrite
from tools.keyVar import KeyVar
from core.messages import Message

file_read = FileRead()
file_write = FileWrite()
key_var = KeyVar()

class StateEngine:    
    def __init__(self, bus):
        self.state_path = key_var.get_state()
        self.message_bus = bus

    async def get_state(self):
        print("----------------------------------------------------------StateEngine get_state")
        state = file_read.read_json_file(self.state_path)
        if not isinstance(state, dict):
            state = {}
        await self.set_state(state)

    async def update_state(self, state):
        ## UPDATE STATE        
        print("----------------------------------------------------------StateEngine update state")
        print('StateEngine TODO UPDATE STATE')
        await self.set_state(state)
        
    async def set_state(self, state):
        print("------------- StateEngine set_state ---- TYPE : StateUpdate")
        await self.message_bus.publish(
            Message(
                id="",
                source="state_engine",
                timestamp="",
                correlation_id="",
                type="StateUpdate",
                data={
                    "state": state
                }))
