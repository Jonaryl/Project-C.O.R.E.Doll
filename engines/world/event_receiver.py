


class EventReceiver:
    def __init__(self, bus):
        self.message_bus = bus
        self.events_messages = []
        self.events_voices = []
        self.events_visions = []
        self.events_actions = []

        self.message_bus.subscribe("WritingConversationMemory", self.receive_user_input)

    def receive_user_input(self, message):      
            event = {
                    "id": message.id,
                    "user": message.data.get("user"),
                    "message": message.data.get("content"),
                    "correlation_id": message.correlation_id,
                    "time": message.timestamp
                    }
            print(" event = ", event)
            self.events_messages.append(event)

    def get_events(self):
        all_events = {
             "messages": self.events_messages,
             "voices": self.events_voices,
             "visions": self.events_visions,
             "actions": self.events_actions
        }
        return all_events

    def clear_event(self):
        self.events_messages.clear()
        self.events_voices.clear()
        self.events_visions.clear()
        self.events_actions.clear()