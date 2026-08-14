import asyncio
from datetime import datetime


from engines.conversation.conversation_prompt import ConversationPrompt
from core.messages import Message
from tools.utils import Utils

conversation_prompt = ConversationPrompt()
utils = Utils()

class ConversationEngine:
    def __init__(self, bus, world, llm):
        self.message_bus = bus
        self.world_engine = world
        self.llm_engine = llm

        self.conversation_prompt = conversation_prompt

        self.input_queue = asyncio.Queue()
        self.handlers = {}

        self.message_bus.subscribe(
            "LLMResponse",
            self.on_llm_response
        )
        self.message_bus.subscribe(
            "UserMessageReceived",
            self.receive_user_input
        )

    async def main(self):
        print("ConversationEngine::main")
        asyncio.create_task(self.message_bus.run())
        asyncio.create_task(self.waiting_message())
        asyncio.create_task(self.llm_engine.run())

    async def waiting_message(self):
        while True:
            user_input = await self.input_queue.get()
            try:
                user = user_input["user"]
                prompt = user_input["prompt"]

                await self.send_message(
                    user,
                    prompt
                )
            except Exception as e:
                print(f"ConversationEngine::waiting_message Erreur : {e}")
                raise
            finally:
                self.input_queue.task_done()

    async def receive_user_input(self, message):
        data = message.data
        user_input = data["content"]
        user = data["user"]

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        request = Message(
                    id=utils.generate_id(),
                    type="LLMRequest",
                    timestamp= timestamp,
                    source="writing_discussion",
                    correlation_id=utils.generate_id_type2(),
                    data={
                        "user": user,
                        "content": user_input,
                    }
                )
        await self.write_message_to_memory(request)



        # TODO
        # async def Run(self):
            # while True:
                # events = self.world_engine.get_events()
                    # try:
        # TODO END

        #self.event_receiver.receive_user_input(user_input=user_input, user=user)

        #events = self.world_engine.get_events()
        #self.world_engine.process_event(events)
        #context = self.world_engine.get_context()

        #### TEMPORARY
        events = []
        events.append({
                    "id": request.id,
                    "user": request.data.get("user"),
                    "message": request.data.get("content"),
                    "correlation_id": request.correlation_id,
                    "time": request.timestamp
                    })
        #### TEMPORARY END  

        prompt = self.get_prompt(events)

        try:
            await self.input_queue.put({
                "user": user,
                "prompt": prompt
            })
            print(f"[Queue] Nombre d'éléments en attente : {self.input_queue.qsize()}")
        except Exception as e:
            print(f"ConversationEngine::receive_user_input Erreur lors de l'ajout dans input_queue : {e}")
    
    async def send_message(self, user, content):
        #print(f"[Conversation] {user}: {content}")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        request = Message(
            id=utils.generate_id(),
            type="LLMRequest",
            timestamp= timestamp,
            source="writing_discussion",
            correlation_id=utils.generate_id_type2(),
            data={
                "user": user,
                "content": content,
            }
        )
        await self.message_bus.publish(request)
        #self.world_engine.clear_event()

    async def on_llm_response(self, message):
        print("on_llm_response ---  message", message)        
        await self.write_message_to_memory(message)

        await self.message_bus.publish(
        Message(
            id="",
            source="",
            timestamp="",
            correlation_id="",
            type="UIUpdate",
            data={
                "action": "refresh_messages",
                "source": "llm"
            }))

    def get_prompt(self, all_events):
        return self.conversation_prompt.create_prompt(all_events)

    async def write_message_to_memory(self, message):   
            response = message.data
            timestamp = message.timestamp

            new_message = Message(
                        id=message.id,
                        source="writing_discussion",
                        timestamp=timestamp,
                        correlation_id=message.correlation_id,
                        type="WritingConversationMemory",
                        data=response)
            
            await self.message_bus.publish(new_message)
