import asyncio
from datetime import datetime


from engines.conversation.conversation_prompt import ConversationPrompt
from core.messages import Message

conversation_prompt = ConversationPrompt()

class ConversationEngine:
    def __init__(self, bus, llm, receiver, world, data):
        self.message_bus = bus
        self.event_receiver = receiver

        self.llm_engine = llm
        self.world_engine = world
        self.data_engine = data

        self.conversation_prompt = conversation_prompt

        self.input_queue = asyncio.Queue()
        self.handlers = {}

        self.message_bus.subscribe(
            "LLMResponse",
            self.on_llm_response
        )

    async def main(self):
        print("ConversationEngine::main")

        asyncio.create_task(self.message_bus.run())
        asyncio.create_task(self.waiting_message())
        asyncio.create_task(self.llm_engine.run())

    def subscribe(self, message_type, handler):
                print("ConversationEngine::subscribe")
                self.handlers.setdefault(message_type, []).append(handler)

    async def waiting_message(self):
        print("ConversationEngine::waiting_message")
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

    async def receive_user_input(self, user_input: str, user: str):
        print("ConversationEngine::receive_user_input")
        self.event_receiver.receive_user_input(user_input=user_input, user=user)
        events = self.event_receiver.get_events()

        self.world_engine.process_event(events)
        context = self.world_engine.get_context()

        prompt = self.get_prompt(events)
        self.write_message_to_memory(user, user_input, False)

        try:
            await self.input_queue.put({
                "user": user,
                "prompt": prompt
            })
            print(f"[Queue] Nombre d'éléments en attente : {self.input_queue.qsize()}")
        except Exception as e:
            print(f"ConversationEngine::receive_user_input Erreur lors de l'ajout dans input_queue : {e}")
    
    async def send_message(self, user, content):
        print("ConversationEngine::send_message")
        #print(f"[Conversation] {user}: {content}")

        request = Message(
            type="LLMRequest",
            data={
                "user": user,
                "content": content,
            }
        )
        await self.message_bus.publish(request)

    async def on_llm_response(self, message):
        response = message.data

        self.write_message_to_memory("IA", response, True)

        #print("ConversationEngine::on_llm_response message =", message)
        #print(f"on_llm_response : [AI] = {response}")

    def get_prompt(self, all_events):
        print("ConversationEngine::get_prompt")
        return self.conversation_prompt.create_prompt(all_events)

    def write_message_to_memory(self, username, message, isDoll):    
            print("ConversationEngine::write_message_to_memory")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
     
            allMessage = []
            if isDoll:
                allMessage.append(self.doll_message(
                         username,
                         message,
                         timestamp))
            else:
                allMessage.append(self.user_message(
                         username,
                         message,
                         timestamp))
                      
            print("All Message :", allMessage)             
            self.data_engine.update_memories(username, allMessage)
            
            handlers = self.handlers.get("ConversationResponse", [])
            for handler in handlers:
                handler()

    def user_message(self, username, message, timestamp):
        return {
                     "user": username,
                     "message": message,
                     "time": timestamp
                 }
    
    def doll_message(self, username, message, timestamp):
        return {
                     "user": username,
                     "message": message,
                     "time": timestamp
                 }