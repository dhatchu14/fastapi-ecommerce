# consumer.py
from confluent_kafka import Consumer, KafkaError
import json
import logging
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaConsumer:
    def __init__(self, bootstrap_servers='kafka:9092', group_id='ecommerce_group'):
        self.consumer = Consumer({
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest'
        })
        self.running = False
        self.handlers = {}
    
    def register_handler(self, event_type, handler_func):
        """
        Register a handler function for a specific event type
        
        Args:
            event_type (str): The event type to handle
            handler_func (callable): Function to call when event is received
        """
        self.handlers[event_type] = handler_func
    
    def subscribe(self, topics):
        """
        Subscribe to Kafka topics
        
        Args:
            topics (list): List of topic names to subscribe to
        """
        self.consumer.subscribe(topics)
    
    def start(self):
        """
        Start consuming messages in a separate thread
        """
        self.running = True
        self.thread = threading.Thread(target=self._consume_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Consumer started and subscribed to topics")
    
    def stop(self):
        """
        Stop the consumer
        """
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=10)
        self.consumer.close()
        logger.info("Consumer stopped")
    
    def _consume_loop(self):
        """
        Main loop for consuming messages
        """
        try:
            while self.running:
                msg = self.consumer.poll(1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info(f"Reached end of partition {msg.partition()}")
                    else:
                        logger.error(f"Error: {msg.error()}")
                    continue
                
                try:
                    value = json.loads(msg.value().decode('utf-8'))
                    event_type = value.get('event_type')
                    
                    if event_type and event_type in self.handlers:
                        self.handlers[event_type](value)
                    else:
                        logger.warning(f"No handler for event type: {event_type}")
                        
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse message: {msg.value()}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            self.running = False