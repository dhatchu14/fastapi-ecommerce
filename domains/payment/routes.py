from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from domains.payment.schema import PaymentCreateSchema, PaymentResponseSchema, PaymentStatusUpdate
from domains.payment.service import PaymentService
from domains.payment.aggregates import PaymentStatus

# Remove the prefix here since it's already defined in main.py
router = APIRouter()

@router.post("/", response_model=PaymentResponseSchema, operation_id="create_payment_unique")
def create_payment(payment: PaymentCreateSchema, db: Session = Depends(get_db)):
    try:
        return PaymentService.process_payment(db, payment)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/{payment_id}", response_model=PaymentResponseSchema)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = PaymentService.get_payment_details(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@router.put("/{payment_id}")
def update_payment_status(
    payment_id: int,
    status: PaymentStatus = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    payment = PaymentService.update_payment_status(db, payment_id, status)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment
    
@router.get("/test")
def test_payment_route():
    return {"message": "Payment route working"}