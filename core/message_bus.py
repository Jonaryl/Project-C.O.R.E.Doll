import asyncio

class MessageBus:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.handlers = {}

    def subscribe(self, message_type, handler):
        print("MessageBus::subscribe")
        self.handlers.setdefault(message_type, []).append(handler)

    async def publish(self, message):
        print("MessageBus::publish")
        await self.queue.put(message)

    async def run(self):
        print("MessageBus::run")
        while True:
            message = await self.queue.get()

            handlers = self.handlers.get(message.type, [])

            for handler in handlers:
                #print("def run ---- message", message)
                await handler(message)

            self.queue.task_done()