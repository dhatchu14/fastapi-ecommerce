from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from domains.customer.models import Customer
from .schemas import CustomerCreate, CustomerResponse, RegisterUser, CustomerCreateResponse
from .service import CustomerService
from db import get_db

router = APIRouter(
    prefix="/customer",
    tags=["customers"]
)

@router.post("/register", response_model=CustomerCreateResponse)
async def register_customer(user_data: RegisterUser, db: Session = Depends(get_db)):
    service = CustomerService(db)
    existing_customer = service.get_customer_by_email(user_data.email)
    
    if existing_customer:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    created_customer = service.create_customer(user_data)
    return CustomerCreateResponse(
        message="Customer registered successfully!",
        customer=created_customer
    )

@router.post("/", response_model=CustomerCreateResponse)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    service = CustomerService(db)
    existing_customer = service.get_customer_by_email(customer.email)

    if existing_customer:
        raise HTTPException(status_code=400, detail="Email already registered")

    created_customer = service.create_customer(customer)
    return CustomerCreateResponse(
        message="Customer registered successfully!",
        customer=created_customer
    )

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    service = CustomerService(db)
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer
