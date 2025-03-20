from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import JSONResponse
from db import get_db
from .service import AuthService, get_current_user
from .schemas import RegisterUser, LoginUser

router = APIRouter()

@router.post("/register")
def register(user_data: RegisterUser, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.register_user(user_data)

@router.post("/login")
def login(request: Request, login_data: LoginUser, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.login_user(request, login_data)

@router.get("/me")
def get_profile(user: dict = Depends(get_current_user)):
    return JSONResponse(content={"username": user["username"], "email": user["email"]})

@router.post("/logout")
def logout(request: Request):
    auth_service = AuthService(None)
    return auth_service.logout_user(request)