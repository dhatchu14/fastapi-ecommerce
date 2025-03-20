# event_distribution.py
import logging
import threading
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from consumer import KafkaConsumer
from producer import KafkaProducer
from event_handlers import InventoryEventHandler, OrderEventHandler, WarehouseEventHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventDistributionSystem:
    """
    Main event distribution system that implements multiple patterns
    """
    def __init__(self, db_url, kafka_servers):
        self.db_engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.db_engine)
        
        # Create producer
        self.producer = KafkaProducer(bootstrap_servers=kafka_servers)
        
        # Create consumers for different event patterns
        self.cdc_consumer = self._create_cdc_consumer(kafka_servers)
        self.command_consumer = self._create_command_consumer(kafka_servers)
        self.event_consumer = self._create_event_consumer(kafka_servers)
        
        # Create event handlers
        db_session = self.Session()
        self.inventory_handler = InventoryEventHandler(db_session)
        self.order_handler = OrderEventHandler(db_session, self.producer)
        self.warehouse_handler = WarehouseEventHandler(db_session)
    
    def _create_cdc_consumer(self, kafka_servers):
        """
        Create a consumer for CDC events from Debezium
        """
        consumer = KafkaConsumer(
            bootstrap_servers=kafka_servers,
            group_id='ecommerce_cdc_group'
        )
        
        # Subscribe to Debezium topics
        consumer.subscribe([
            'ecommerce.public.users',
            'ecommerce.public.customers',
            'ecommerce.public.warehouses',
            'ecommerce.public.inventory',
            'ecommerce.public.orders',
            'ecommerce.public.payments'
        ])
        
        # Register handlers for CDC events
        consumer.register_handler('c', self._handle_create)
        consumer.register_handler('u', self._handle_update)
        consumer.register_handler('d', self._handle_delete)
        
        return consumer
    
    def _create_command_consumer(self, kafka_servers):
        """
        Create a consumer for command pattern events
        """
        consumer = KafkaConsumer(
            bootstrap_servers=kafka_servers,
            group_id='ecommerce_command_group'
        )
        
        # Subscribe to command topics
        consumer.subscribe([
            'inventory_commands',
            'order_commands',
            'payment_commands'
        ])
        
        # Register handlers for commands
        consumer.register_handler('reserve_inventory', self._handle_reserve_inventory)
        consumer.register_handler('process_payment', self._handle_process_payment)
        
        return consumer
    
    def _create_event_consumer(self, kafka_servers):
        """
        Create a consumer for event-driven pattern
        """
        consumer = KafkaConsumer(
            bootstrap_servers=kafka_servers,
            group_id='ecommerce_event_group'
        )
        
        # Subscribe to event topics
        consumer.subscribe([
            'order_events',
            'inventory_events',
            'payment_events'
        ])
        
        # Register handlers for events
        consumer.register_handler('order_created', self.order_handler.handle_order_created)
        consumer.register_handler('payment_processed', self.order_handler.handle_payment_processed)
        consumer.register_handler('inventory_updated', self.inventory_handler.handle_inventory_updated)
        consumer.register_handler('order_ready_for_fulfillment', self.warehouse_handler.handle_order_ready_for_fulfillment)
        
        return consumer
    
    def _handle_create(self, event):
        """
        Handle CDC create events
        """
        source_table = event.get('source', {}).get('table')
        payload = event.get('payload', {})
        
        logger.info(f"CDC Create event: {source_table} - {payload.get('id')}")
        
        # Transform CDC event to domain event
        if source_table == 'orders':
            self.producer.publish_event(
                topic='order_events',
                event_type='order_created',
                payload=payload,
                key=str(payload.get('id'))
            )
        elif source_table == 'inventory':
            self.producer.publish_event(
                topic='inventory_events',
                event_type='inventory_created',
                payload=payload,
                key=str(payload.get('id'))
            )
        # Add more mappings as needed
    
    def _handle_update(self, event):
        """
        Handle CDC update events
        """
        source_table = event.get('source', {}).get('table')
        payload = event.get('payload', {})
        
        logger.info(f"CDC Update event: {source_table} - {payload.get('id')}")
        
        # Transform CDC event to domain event
        if source_table == 'inventory':
            self.producer.publish_event(
                topic='inventory_events',
                event_type='inventory_updated',
                payload=payload,
                key=str(payload.get('id'))
            )
        elif source_table == 'orders':
            self.producer.publish_event(
                topic='order_events',
                event_type='order_updated',
                payload=payload,
                key=str(payload.get('id'))
            )
        # Add more mappings as needed
    
    def _handle_delete(self, event):
        """
        Handle CDC delete events
        """
        source_table = event.get('source', {}).get('table')
        payload = event.get('payload', {})
        
        logger.info(f"CDC Delete event: {source_table} - {payload.get('id')}")
        
        # Transform CDC event to domain event based on table
        # Add specific logic as needed
    
    def _handle_reserve_inventory(self, event):
        """
        Handle inventory reservation command
        """
        payload = event.get('payload', {})
        order_id = payload.get('order_id')
        item_id = payload.get('item_id')
        quantity = payload.get('quantity')
        
        logger.info(f"Reserving {quantity} units of item {item_id} for order {order_id}")
        
        # Implement inventory reservation logic
        # This could update a database or call a service
        
        # Publish result event
        self.producer.publish_event(
            topic='inventory_events',
            event_type='inventory_reserved',
            payload={
                'order_id': order_id,
                'item_id': item_id,
                'quantity': quantity,
                'status': 'reserved'  # or 'failed' if not enough inventory
            },
            key=str(item_id)
        )
    
    def _handle_process_payment(self, event):
        """
        Handle payment processing command
        """
        payload = event.get('payload', {})
        order_id = payload.get('order_id')
        amount = payload.get('amount')
        
        logger.info(f"Processing payment of ${amount} for order {order_id}")
        
        # Implement payment processing logic
        # This could call a payment gateway or service
        
        # Publish result event
        self.producer.publish_event(
            topic='payment_events',
            event_type='payment_processed',
            payload={
                'order_id': order_id,
                'amount': amount,
                'status': 'successful'  # or 'failed' if payment fails
            },
            key=str(order_id)
        )
    
    def start(self):
        """
        Start the event distribution system
        """
        logger.info("Starting Event Distribution System")
        
        # Start all consumers
        self.cdc_consumer.start()
        self.command_consumer.start()
        self.event_consumer.start()
        
        logger.info("Event Distribution System started")
    
    def stop(self):
        """
        Stop the event distribution system
        """
        logger.info("Stopping Event Distribution System")
        
        # Stop all consumers
        self.cdc_consumer.stop()
        self.command_consumer.stop()
        self.event_consumer.stop()
        
        # Flush any remaining messages
        self.producer.flush()
        
        logger.info("Event Distribution System stopped")