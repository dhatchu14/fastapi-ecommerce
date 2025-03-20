from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# PostgreSQL Database Configuration
# Use environment variable if available, otherwise use a default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:root@postgres:5432/ecommerce_db")

# SQLAlchemy Engine
engine = create_engine(DATABASE_URL)

# Base class for models
Base = declarative_base()

# Session Maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Import all models BEFORE creating tables
from domains.inventory.models import Warehouse, Inventory, InventoryItem, StockLevel
from domains.order.models import Order, OrderItem, OrderTracking

def reset_database():
    """Drop existing tables and recreate them."""
    try:
        with engine.connect() as connection:
            connection.execute(text("DROP SCHEMA public CASCADE;"))
            connection.execute(text("CREATE SCHEMA public;"))
            connection.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
            connection.execute(text("GRANT ALL ON SCHEMA public TO public;"))
            connection.commit()
        
        print("Database schema reset successfully")

        # ✅ Ensure all tables are created
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully")

    except Exception as e:
        print(f"Error during database reset: {e}")
        raise

def create_tables():
    """Create all tables based on the defined SQLAlchemy models."""
    Base.metadata.create_all(bind=engine)
    print("Inventory and Order tables created successfully!")

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()