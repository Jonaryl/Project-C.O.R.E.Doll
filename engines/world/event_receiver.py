


class EventReceiver:
    def __init__(self):
        self.events_messages = []
        self.events_voices = []
        self.events_visions = []
        self.events_actions = []

    def receive_user_input(self, user_input: str, user: str) -> str:        
            print("User :", user)
            print("Message :", user_input)

            event = {
                "type": "user_input",
                "content": user_input,
                "user": user
            }
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