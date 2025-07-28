class PubSub:
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type: str, callback):
        """Register a callback for a specific event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type: str, data=None):
        """Notify all subscribers of an event."""
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(data)