# producer.py
import time
from confluent_kafka import Producer
import json
import socket
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self, bootstrap_servers='kafka:9092'):
        self.producer = Producer({
            'bootstrap.servers': bootstrap_servers,
            'client.id': socket.gethostname()
        })
    
    def publish_event(self, topic, event_type, payload, key=None):
        """
        Publish an event to a Kafka topic
        
        Args:
            topic (str): Kafka topic name
            event_type (str): Type of event (e.g., 'order_created', 'inventory_updated')
            payload (dict): Event data
            key (str, optional): Event key for partitioning
        """
        message = {
            'event_type': event_type,
            'payload': payload,
            'timestamp': int(time.time() * 1000)
        }
        
        try:
            self.producer.produce(
                topic=topic,
                key=key.encode('utf-8') if key else None,
                value=json.dumps(message).encode('utf-8'),
                callback=self._delivery_report
            )
            # Trigger any available delivery callbacks
            self.producer.poll(0)
        except Exception as e:
            logger.error(f"Error producing message to {topic}: {e}")
    
    def _delivery_report(self, err, msg):
        """
        Called once for each message produced to indicate delivery result.
        """
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")
    
    def flush(self):
        """
        Wait for all messages in the Producer queue to be delivered.
        """
        self.producer.flush()