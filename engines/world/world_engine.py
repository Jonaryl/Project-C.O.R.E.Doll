
from engines.world.event_receiver import EventReceiver


class WorldEngine:
    def __init__(self, bus):
        self.state = {}
        self.message_bus = bus
        self.event_receiver = EventReceiver(self.message_bus)

        self.temporary_memory = []
        self.message_bus.subscribe("TemporaryMemoryUpdate", self.update_temporary_memory)
        self.message_bus.subscribe("StateUpdate", self.update_state)


    def process_event(self, event):
        # modifier self.state
        pass

    def get_context(self):
        return {
            "temporary_memory": self.temporary_memory,
            "state": self.state
        }

    def get_events(self):
        return self.event_receiver.get_events()

    def clear_event(self):
        self.event_receiver.clear_event()

    def update_temporary_memory(self, memories):
        for memory in memories.data["temporary_memories"]:
            self.temporary_memory.append(memory)

    def update_state(self, message):
        state = message.data["state"]
        self.state = state
