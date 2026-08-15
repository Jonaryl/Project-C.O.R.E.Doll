import asyncio
from engines.data.memory_engine import MemoryEngine
from engines.data.state_engine import StateEngine

class DataEngine:
    def __init__(self, bus):
        self.message_bus = bus
        self.memory_engine = MemoryEngine(self.message_bus)
        self.state_engine = StateEngine(self.message_bus)

        self.message_bus.subscribe("WritingConversationMemory", self.update_memories)
        self.message_bus.subscribe("EditState", self.update_state)

    async def main(self):
        await self.get_temporary_memories()
        await self.get_state()


    async def get_state(self):
        await self.state_engine.get_state()
    async def update_state(self, state):
        await self.state_engine.update_state(state)


    async def update_memories(self, message):
        await self.memory_engine.update_memories(message)
    async def get_temporary_memories(self):
        await self.memory_engine.get_temporary_memories()
