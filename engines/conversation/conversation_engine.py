from engines.conversation.conversation_prompt import ConversationPrompt
from core.messages import Message

conversation_prompt = ConversationPrompt()

class ConversationEngine:
    def __init__(self, bus):
        self.message_bus = bus
        self.conversation_prompt = conversation_prompt

        self.message_bus.subscribe(
            "LLMResponse",
            self.on_llm_response
        )
    
    async def send_message(self, user, content):
        print("LLMEngine::send_message")
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
        print("LLMEngine::on_llm_response")
        response = message.data["content"]
        print(f"on_llm_response : [AI] {response}")


    def get_prompt(self, all_events):
        print("ConversationEngine::get_prompt")
        return self.conversation_prompt.create_prompt(all_events)