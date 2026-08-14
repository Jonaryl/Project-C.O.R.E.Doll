import asyncio
import ollama
from datetime import datetime

from core.messages import Message
from tools.utils import Utils

utils = Utils()

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
        await self.request_queue.put(message)

    async def run(self):
        while True:
            message = await self.request_queue.get()
            try:
                response = await self.generate(message)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

                await self.message_bus.publish(
                    Message(
                        id=utils.generate_id(),
                        timestamp= timestamp,
                        source="writing_discussion",
                        correlation_id=utils.generate_id_type2(),
                        type="LLMResponse",
                        data={
                            "user":"IA",
                            "content":response
                        }
                    )
                )
            except Exception as e:
                print(f"LLMEngine::run ERROR : {e}")
            finally:
                self.request_queue.task_done()

    async def generate(self, message):
        #print(f"model: {self.model}")
        data = message.data
        prompt = data["content"] 
        
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, lambda:  ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            options={
            'temperature': 0.7,
            'num_ctx': 8192
            }
        ))
        print(f"prompt : {prompt}")
        print("LLMEngine::generate response", response)
        #print("response", response["message"]["content"])
        #print("thinking", response["message"]["thinking"])

        return response["message"]["content"]