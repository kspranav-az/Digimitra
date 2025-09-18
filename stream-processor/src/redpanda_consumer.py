import os
import json
from kafka import KafkaConsumer

class RedpandaConsumer:
    def __init__(self, topic, handler_func):
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=os.environ.get("REDPANDA_BOOTSTRAP"),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='my-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8')))
        self.handler_func = handler_func

    def start_consuming(self):
        for message in self.consumer:
            self.handler_func(message.value)
