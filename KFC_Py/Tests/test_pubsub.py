from PubSub import PubSub

def test_pubsub():
    pubsub = PubSub()
    results = []

    def callback(data):
        results.append(data)

    pubsub.subscribe("test_event", callback)
    pubsub.publish("test_event", {"key": "value"})

    assert results == [{"key": "value"}]