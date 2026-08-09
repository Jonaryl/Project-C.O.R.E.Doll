



class WorldEngine:
    def __init__(self, event_receiver):
        self.state = {}
        self.event_receiver = event_receiver

    def process_event(self, event):
        # modifier self.state
        pass

    def get_context(self):
        return self.state