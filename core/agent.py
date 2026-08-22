import asyncio
import threading

from engines.conversation.conversation_engine import ConversationEngine
from engines.world.world_engine import WorldEngine
from engines.data.data_engine import DataEngine

from engines.perception.perception_engine import PerceptionEngine

from core.message_bus import MessageBus
from core.messages import Message
from core.Llm import LLMEngine

from tools.keyVar import KeyVar

key_var = KeyVar()
class Agent:
    def __init__(self):
        self.stop_event = threading.Event()
        self.model = key_var.get_conversation_model()
        self.message_bus = MessageBus()

        self.world_engine = WorldEngine(self.message_bus)
        self.data_engine = DataEngine(self.message_bus)
        self.perception_engine = PerceptionEngine(self.message_bus)


        self.llm_engine = LLMEngine(self.message_bus, self.model)
        self.conversation_engine = ConversationEngine(self.message_bus, self.world_engine, self.llm_engine)
        self.loop = None

        self.ui_callbacks = [] 
        self.message_bus.subscribe("UIUpdate", self.on_ui_update)


    async def main(self):
        self.loop = asyncio.get_running_loop()
        await self.conversation_engine.main()
        await self.data_engine.main()
        await self.perception_engine.main()

    def stop(self):
        print("Agent.stop()")
        self.stop_event.set()
        if hasattr(self, "perception_engine"):
            self.perception_engine.stop()
    
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