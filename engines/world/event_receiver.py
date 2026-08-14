import asyncio


class EventReceiver:
    def __init__(self, bus):
        self.message_bus = bus
        self.event_queue = asyncio.Queue()
        self.message_bus.subscribe("WritingConversationEvent", self.receive_user_input)

    async def receive_user_input(self, message):
            print(" -------  EventReceiver::receive_user_input ------- user = ", message.data.get("user"))  
            event = {
                    "id": message.id,
                    "user": message.data.get("user"),
                    "message": message.data.get("content"),
                    "correlation_id": message.correlation_id,
                    "time": message.timestamp,
                    "type": "user_input"   
                    }
            print(" event = ", event)
            await self.event_queue.put(event)

    async def get_events(self):
        events = []

        first = await self.event_queue.get()
        events.append(first)

        while not self.event_queue.empty():
            events.append(self.event_queue.get_nowait())

        return {
            "messages": [e for e in events if e.get("type") == "user_input"],
            "voices": [],
            "visions": [],
            "actions": []
        }

    def clear_event(self):
        self.events_messages.clear()
        self.events_voices.clear()
        self.events_visions.clear()
        self.events_actions.clear()