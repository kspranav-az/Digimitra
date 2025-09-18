import os
import json
from kafka import KafkaProducer

class RedpandaProducer:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=os.environ.get("REDPANDA_BOOTSTRAP"),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def produce_event(self, topic, event):
        self.producer.send(topic, event)
