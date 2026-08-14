import asyncio
from engines.data.memory_engine import MemoryEngine


class DataEngine:
    def __init__(self, bus):
        self.message_bus = bus
        self.memory_engine = MemoryEngine()

        self.message_bus.subscribe("WritingConversationMemory", self.update_memories)

    async def update_memories(self, message):
        print("DATA ENGINE :: update_memories")
        self.memory_engine.add_to_discussion(message)