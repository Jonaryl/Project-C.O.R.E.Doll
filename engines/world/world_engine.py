
from engines.world.event_receiver import EventReceiver


class WorldEngine:
    def __init__(self, bus):
        self.state = {}
        self.message_bus = bus
        self.event_receiver = EventReceiver(self.message_bus)

    def process_event(self, event):
        # modifier self.state
        pass

    def get_context(self):
        return self.state

    def get_events(self):
        return self.event_receiver.get_events()

    def clear_event(self):
        self.event_receiver.clear_event()