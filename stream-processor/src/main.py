import logging
from redpanda_consumer import RedpandaConsumer
from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventProcessor:
    """
    Coordinates the consumption of events and their storage in the database.
    """
    def __init__(self):
        self.database = Database()
        self.consumer = RedpandaConsumer(
            topic="events",
            handler_func=self.handle_event_message
        )

    def handle_event_message(self, message: dict):
        """
        The callback function passed to the Redpanda consumer.
        It receives a message, logs it, and inserts it into the database.
        """
        logger.info(f"Processing event: {message.get('event_id')}")
        self.database.insert_event(message)

    def run(self):
        """
        Starts the event processing loop.
        """
        logger.info("Starting Stream Processor...")
        self.consumer.start_consuming()

if __name__ == "__main__":
    processor = EventProcessor()
    processor.run()
