from fastapi import FastAPI, BackgroundTasks
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging

# Import route modules
from domains.authentication.routes import router as auth_router
from domains.customer.routes import router as customer_router
from domains.payment.routes import router as payment_router
from domains.order.routes import router as order_router

# Import the corrected routers from inventory
from domains.inventory.routes import inventory_router
from domains.inventory.routes import products_router
from domains.inventory.routes import warehouse_router

# Import database initialization
from db import create_tables, reset_database

# Import event distribution system components
from event_distribution import EventDistributionSystem
from producer import KafkaProducer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/ecommerce")
KAFKA_SERVERS = os.getenv("KAFKA_SERVERS", "kafka:9092")

# Initialize Kafka producer
try:
    kafka_producer = KafkaProducer(bootstrap_servers=KAFKA_SERVERS)
    logger.info("Kafka producer initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Kafka producer: {e}")
    kafka_producer = None

# Initialize FastAPI app
app = FastAPI(
    title="E-commerce API",
    description="API for customer management, authentication, orders, payments, inventory with event distribution",
    version="1.0.0"
)

# Create database tables
create_tables()
try:
    reset_database()
    logger.info("Database reset and initialization successful")
except Exception as e:
    logger.error(f"Error during database reset: {e}")
    logger.info("Attempting to create tables without reset...")
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

# Initialize event distribution system
try:
    event_system = EventDistributionSystem(
        db_url=DATABASE_URL,
        kafka_servers=KAFKA_SERVERS
    )
    logger.info("Event distribution system initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize event distribution system: {e}")
    event_system = None

# Middleware for session handling
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Start the event distribution system on application startup"""
    logger.info("Starting up the application")
    if event_system:
        try:
            event_system.start()
            logger.info("Event distribution system started successfully")
        except Exception as e:
            logger.error(f"Failed to start event distribution system: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the event distribution system on application shutdown"""
    logger.info("Shutting down the application")
    if event_system:
        try:
            event_system.stop()
            logger.info("Event distribution system stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop event distribution system: {e}")

@app.get("/", tags=["Health Check"])
async def root():
    """Check API health."""
    return {"message": "API is running 🚀"}

# Helper function to publish events
def publish_event(topic, event_type, payload, key=None):
    """Publish an event to Kafka if the producer is available"""
    if kafka_producer:
        try:
            kafka_producer.publish_event(topic, event_type, payload, key)
            logger.info(f"Event published: {event_type} to {topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
    return False

# Register Routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(customer_router, prefix="/customers", tags=["Customers"])
app.include_router(payment_router, prefix="/payments", tags=["Payments"])
app.include_router(order_router, prefix="/orders", tags=["Orders"])

# Register inventory-related routers with proper prefixes
app.include_router(inventory_router, prefix="/inventory", tags=["Inventory"])
app.include_router(products_router, prefix="/products", tags=["Products"])
app.include_router(warehouse_router, prefix="/warehouses", tags=["Warehouses"])

# Add background task dependencies to routes
# This example shows how to modify an existing route to include event publishing
@app.post("/orders/", tags=["Orders"])
async def create_order(order_data: dict, background_tasks: BackgroundTasks):
    """Create a new order and publish an event"""
    # Call the original order creation function
    # (This is a placeholder - you'll need to integrate with your actual order creation logic)
    order_id = "123"  # This would be the actual order ID from your order creation logic
    
    # Publish event in the background
    background_tasks.add_task(
        publish_event,
        topic="order_events",
        event_type="order_created",
        payload=order_data,
        key=str(order_id)
    )
    
    return {"order_id": order_id, "message": "Order created successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)