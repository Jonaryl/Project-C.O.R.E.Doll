import traceback
import asyncio
import inspect

class MessageBus:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.handlers = {}

    def subscribe(self, message_type, handler):
        self.handlers.setdefault(message_type, []).append(handler)

    async def publish(self, message):
        await self.queue.put(message)

    async def run(self):
        while True:
            message = await self.queue.get()
            try:
                handlers = self.handlers.get(message.type, [])

                for handler in handlers:
                    #print(f"  → handler = {handler}  (type={type(handler)})")  # debug

                    if inspect.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        result = handler(message)
                        if asyncio.iscoroutine(result):
                            await result
            except Exception as e:
                print(f"MessageBus::run ERROR on {message.type}: {e}")
                traceback.print_exc()
            finally:
                self.queue.task_done()