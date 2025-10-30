import json
from ..cache.redis import redis_client

def publish(topic: str, payload: dict):
    redis_client.publish(topic, json.dumps(payload))

def subscribe(topic: str):
    pubsub = redis_client.pubsub()
    pubsub.subscribe(topic)
    return pubsub
