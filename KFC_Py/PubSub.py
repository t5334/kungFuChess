# PubSub.py

class PubSub:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PubSub, cls).__new__(cls)
            cls._instance.subscribers = {}
        return cls._instance

    def subscribe(self, event_type: str, callback):
        """רישום לפעולה מסוימת"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type: str, data=None):
        """שיגור הודעה לכל מי שמחכה לאירוע מסוים"""
        for callback in self.subscribers.get(event_type, []):
            callback(data)

pubsub = PubSub()