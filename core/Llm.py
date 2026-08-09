import asyncio
import ollama
from core.messages import Message


class LLMEngine:

    def __init__(self, bus):
        self.bus = bus
        self.client = ollama.Client()

        bus.subscribe(
            "LLMRequest",
            self.on_request
        )

    async def on_request(self, message):
        print("LLMEngine::on_request")
        data = message.data
        prompt = data["content"]

        response = await self.generate(prompt)

        await self.bus.publish(
            Message(
                type="LLMResponse",
                data={
                    "content": response
                }
            )
        )

    async def generate(self, prompt, model):
        print("LLMEngine::generate")
        print(f"model: {model}")
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={
            'temperature': 0.7,
            'num_ctx': 8192
        }
        )
        print(f"Réponse du modèle à : {prompt}")
        print("response", response)
        return response["message"]["content"]