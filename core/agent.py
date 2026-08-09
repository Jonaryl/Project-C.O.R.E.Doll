import asyncio
from engines.conversation.conversation_engine import ConversationEngine
from engines.world.world_engine import WorldEngine
from engines.world.event_receiver import EventReceiver

from core.message_bus import MessageBus
from core.Llm import LLMEngine



class Agent:
    def __init__(self):
        self.event_receiver = EventReceiver()
        self.world_engine = WorldEngine(event_receiver=self.event_receiver)

        self.message_bus = MessageBus()

        self.message_count = 0
        self.user = ""
        self.prompt = ""


    async def main(self):
        print("Agent::main")
        self.conversation_engine = ConversationEngine(self.message_bus)
        self.llm_engine = LLMEngine(self.message_bus)

        asyncio.create_task(self.message_bus.run())
        asyncio.create_task(self.waiting_message())

    async def waiting_message(self):
        print("Agent::waiting_message")
        while True:
            if self.message_count != 0 and self.user != "" and self.prompt != "":
                print("self.message_count", self.message_count)
                await self.conversation_engine.send_message(self.user, self.prompt)

                self.message_count -= 1
                self.user = ""
                self.prompt = ""


    def receive_user_input(self, user_input: str, user: str):
        print("Agent::receive_user_input")
        self.event_receiver.receive_user_input(user_input=user_input, user=user)
        events = self.event_receiver.get_events()

        self.world_engine.process_event(events)
        context = self.world_engine.get_context()

        prompt = self.conversation_engine.get_prompt(events)
        self.user = user
        self.prompt = prompt
        self.message_count += 1
        print("receive_user_input self.message_count", self.message_count)



