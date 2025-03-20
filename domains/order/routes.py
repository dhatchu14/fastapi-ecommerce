from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from db import get_db
from domains.order.service import OrderService
from domains.order.schemas import OrderCreateSchema, OrderSchema, OrderUpdate
from main import publish_event  # Import event publishing function

router = APIRouter()

@router.post("/", response_model=OrderSchema, status_code=201)
def create_order(order_data: OrderCreateSchema, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create a new order and publish an event"""
    try:
        order_service = OrderService(db)
        db_order = order_service.create_order(order_data)
        
        # Publish event in the background
        background_tasks.add_task(
            publish_event,
            topic="order_events",
            event_type="order_created",
            payload=db_order.dict(),
            key=str(db_order.id)
        )

        return db_order
    except Exception as e:
        print(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{order_id}", response_model=OrderSchema)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Retrieve an order by ID"""
    order_service = OrderService(db)
    db_order = order_service.get_order(order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order

@router.put("/{order_id}", response_model=OrderSchema)
def update_order(order_id: int, order_data: OrderUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Update an order and publish an event"""
    order_service = OrderService(db)
    db_order = order_service.update_order(order_id, order_data)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Publish event in the background
    background_tasks.add_task(
        publish_event,
        topic="order_events",
        event_type="order_updated",
        payload=db_order.dict(),
        key=str(db_order.id)
    )

    return db_order

@router.put("/{order_id}/status", response_model=OrderSchema)
def update_order_status(order_id: int, status: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Update an order's status and publish an event"""
    order_service = OrderService(db)
    db_order = order_service.update_order_status(order_id, status)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Publish event in the background
    background_tasks.add_task(
        publish_event,
        topic="order_events",
        event_type="order_status_updated",
        payload={"order_id": order_id, "status": status},
        key=str(order_id)
    )

    return db_order

@router.delete("/{order_id}", response_model=dict, status_code=204)
def delete_order(order_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Delete an order and publish an event"""
    order_service = OrderService(db)
    result = order_service.delete_order(order_id)
    if not result:
        raise HTTPException(status_code=404, detail="Order not found")

    # Publish event in the background
    background_tasks.add_task(
        publish_event,
        topic="order_events",
        event_type="order_deleted",
        payload={"order_id": order_id},
        key=str(order_id)
    )

    return {"message": "Order deleted successfully"}
