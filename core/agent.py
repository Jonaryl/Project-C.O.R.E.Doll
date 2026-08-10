import asyncio
from engines.conversation.conversation_engine import ConversationEngine
from engines.world.world_engine import WorldEngine
from engines.world.event_receiver import EventReceiver

from core.message_bus import MessageBus
from core.Llm import LLMEngine



class Agent:
    def __init__(self):
        self.model = "qwen3:8b"
        self.event_receiver = EventReceiver()
        self.world_engine = WorldEngine(event_receiver=self.event_receiver)

        self.message_bus = MessageBus()

        self.llm_engine = LLMEngine(self.message_bus, self.model)
        self.conversation_engine = ConversationEngine(self.message_bus, self.llm_engine, self.event_receiver, self.world_engine)

    async def main(self):
        print("Agent::main")
        await self.conversation_engine.main()


    async def receive_user_input(self, user_input: str, user: str):
         await self.conversation_engine.receive_user_input(user_input, user)



