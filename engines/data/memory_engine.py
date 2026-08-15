import asyncio
from tools.file_r import FileRead
from tools.file_w import FileWrite
from tools.keyVar import KeyVar
from core.messages import Message

file_read = FileRead()
file_write = FileWrite()
key_var = KeyVar()


class MemoryEngine:
    def __init__(self, bus):
        self.discussion_path = key_var.get_message_json()
        self.message_bus = bus

    async def add_to_discussion(self, message):
        entry = {
        "id": message.id,
        "user": message.data.get("user"),
        "message": message.data.get("content"),
        "correlation_id": message.correlation_id,
        "time": message.timestamp
        }

        file_write.write_json(self.discussion_path, entry)
        return entry
          
    async def get_temporary_memories(self):
        temporary_memories = file_read.read_json_file(self.discussion_path)
        await self.set_temporary_memory(temporary_memories)

    async def update_memories(self, message):
            temporary_memories = []
            entry = await self.add_to_discussion(message)
            temporary_memories.append(entry)
            await self.set_temporary_memory(temporary_memories)

    async def set_temporary_memory(self, temporary_memories):
        await self.message_bus.publish(
            Message(
                id="",
                source="",
                timestamp="",
                correlation_id="",
                type="TemporaryMemoryUpdate",
                data={
                    "temporary_memories": temporary_memories
                }))