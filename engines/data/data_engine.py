from engines.data.memory_engine import MemoryEnigine


class DataEngine:
    def __init__(self):
        self.memory_engine = MemoryEnigine()

    def update_memories(self, username, message):
        print(message)
        self.memory_engine.add_to_discussion(username, message)