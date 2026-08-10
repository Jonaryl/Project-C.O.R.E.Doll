import asyncio
from engines.conversation.conversation_prompt import ConversationPrompt
from core.messages import Message

conversation_prompt = ConversationPrompt()

class ConversationEngine:
    def __init__(self, bus, llm, receiver, world):
        self.message_bus = bus
        self.llm_engine = llm
        self.event_receiver = receiver
        self.world_engine = world
        self.conversation_prompt = conversation_prompt

        self.input_queue = asyncio.Queue()

        self.message_bus.subscribe(
            "LLMResponse",
            self.on_llm_response
        )

    async def main(self):
        print("ConversationEngine::main")

        asyncio.create_task(self.message_bus.run())
        asyncio.create_task(self.waiting_message())
        asyncio.create_task(self.llm_engine.run())


    async def waiting_message(self):
        print("ConversationEngine::waiting_message")
        while True:
            user_input = await self.input_queue.get()
            print(f"ConversationEngine::waiting_message Taille restante : {self.input_queue.qsize()}")
            try:
                user = user_input["user"]
                prompt = user_input["prompt"]

                await self.conversation_engine.send_message(
                    user,
                    prompt
                )
                print(f"ConversationEngine::waiting_message Envoi terminé pour {user}")
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
        print(f"[Conversation] {user}: {content}")

        request = Message(
            type="LLMRequest",
            data={
                "user": user,
                "content": content,
            }
        )
        await self.message_bus.publish(request)

    async def on_llm_response(self, message):
        print("ConversationEngine::on_llm_response")
        response = message.data["content"]
        print(f"on_llm_response : [AI] {response}")

    def get_prompt(self, all_events):
        print("ConversationEngine::get_prompt")
        return self.conversation_prompt.create_prompt(all_events)