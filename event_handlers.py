# event_handlers.py
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InventoryEventHandler:
    """
    Handles inventory-related events
    """
    def __init__(self, db_session):
        self.db_session = db_session
    
    def handle_inventory_updated(self, event):
        """
        Handle inventory update events
        """
        payload = event.get('payload', {})
        item_id = payload.get('id')
        quantity = payload.get('quantity')
        
        logger.info(f"Inventory updated: Item {item_id} now has {quantity} units")
        
        # Implement inventory logic here
        # For example, trigger alerts if stock is low
        if quantity < 10:
            self.trigger_low_stock_alert(item_id, quantity)
    
    def trigger_low_stock_alert(self, item_id, quantity):
        """
        Trigger an alert for low stock
        """
        logger.warning(f"LOW STOCK ALERT: Item {item_id} has only {quantity} units left")
        # Additional logic for sending notifications, etc.


class OrderEventHandler:
    """
    Handles order-related events
    """
    def __init__(self, db_session, kafka_producer):
        self.db_session = db_session
        self.kafka_producer = kafka_producer
    
    def handle_order_created(self, event):
        """
        Handle order creation events
        """
        payload = event.get('payload', {})
        order_id = payload.get('id')
        customer_id = payload.get('customer_id')
        items = payload.get('items', [])
        
        logger.info(f"New order {order_id} received for customer {customer_id}")
        
        # Command pattern: issue command to update inventory
        for item in items:
            self.kafka_producer.publish_event(
                topic='inventory_commands',
                event_type='reserve_inventory',
                payload={
                    'order_id': order_id,
                    'item_id': item['id'],
                    'quantity': item['quantity']
                },
                key=str(item['id'])
            )
        
        # Publish event for other services
        self.kafka_producer.publish_event(
            topic='order_events',
            event_type='order_processing_started',
            payload={
                'order_id': order_id,
                'customer_id': customer_id,
                'timestamp': datetime.now().isoformat()
            },
            key=str(order_id)
        )
    
    def handle_payment_processed(self, event):
        """
        Handle payment processed events
        """
        payload = event.get('payload', {})
        order_id = payload.get('order_id')
        payment_status = payload.get('status')
        
        logger.info(f"Payment for order {order_id} processed with status: {payment_status}")
        
        if payment_status == 'successful':
            # Update order status
            # Trigger fulfillment process
            self.kafka_producer.publish_event(
                topic='order_events',
                event_type='order_ready_for_fulfillment',
                payload={
                    'order_id': order_id,
                    'timestamp': datetime.now().isoformat()
                },
                key=str(order_id)
            )


class WarehouseEventHandler:
    """
    Handles warehouse and fulfillment events
    """
    def __init__(self, db_session):
        self.db_session = db_session
    
    def handle_order_ready_for_fulfillment(self, event):
        """
        Handle order fulfillment events
        """
        payload = event.get('payload', {})
        order_id = payload.get('order_id')
        
        logger.info(f"Preparing order {order_id} for fulfillment")
        
        # Implement warehouse logic here
        # For example, select the best warehouse for fulfillment
        # Create picking lists, etc.