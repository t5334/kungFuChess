from PubSub import pubsub

def test_pubsub():
    results = []

    def callback(data):
        results.append(data)

    pubsub.subscribe("test_event", callback)
    pubsub.publish("test_event", {"key": "value"})

    assert results == [{"key": "value"}]