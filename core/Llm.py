import asyncio
import ollama
from core.messages import Message


class LLMEngine:

    def __init__(self, bus, model):
        self.message_bus = bus
        self.model = model
        self.client = ollama.Client()
        
        self.request_queue = asyncio.Queue()

        self.message_bus.subscribe(
            "LLMRequest",
            self.enqueue_request
        )


    async def enqueue_request(self, message):
        print("LLMEngine::enqueue_request")
        await self.request_queue.put(message)


    async def run(self):
        print("LLMEngine::run")
        while True:
            message = await self.request_queue.get()
            try:
                response = await self.generate(message)

                await self.message_bus.publish(
                    Message(
                        type="LLMResponse",
                        data=response
                    )
                )
            finally:
                self.request_queue.task_done()

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
        #print("response", response["message"]["content"])
        #print("thinking", response["message"]["thinking"])

        return response["message"]["content"]