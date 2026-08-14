import asyncio
from engines.conversation.conversation_engine import ConversationEngine
from engines.world.world_engine import WorldEngine
from engines.data.data_engine import DataEngine

from core.message_bus import MessageBus
from core.messages import Message
from core.Llm import LLMEngine

class Agent:
    def __init__(self):
        self.model = "qwen3:8b"
        self.message_bus = MessageBus()

        self.world_engine = WorldEngine(self.message_bus)
        self.data_engine = DataEngine(self.message_bus)


        self.llm_engine = LLMEngine(self.message_bus, self.model)
        self.conversation_engine = ConversationEngine(self.message_bus, self.world_engine, self.llm_engine)
        self.loop = None

        self.ui_callbacks = [] 
        self.message_bus.subscribe("UIUpdate", self.on_ui_update)


    async def main(self):
        self.loop = asyncio.get_running_loop()
        await self.conversation_engine.main()

    async def receive_user_input(self, user_input: str, user: str):
        await self.message_bus.publish(
            Message(
                id="",
                source="",
                timestamp="",
                correlation_id="",
                type="UserMessageReceived",
                data={
                    "user": user,
                    "content": user_input
                }))

    def register_ui_callback(self, callback):
        self.ui_callbacks.append(callback)

    async def on_ui_update(self, message):
        data = message.data
        for callback in self.ui_callbacks:
            callback(data)