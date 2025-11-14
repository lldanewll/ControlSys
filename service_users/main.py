from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from .database_config import get_db
from .database import User
from .schemas import UserCreate, UserResponse, UserUpdate

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="Users Service", 
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "Users service is running"}

@app.post("/v1/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # TODO: Реализовать регистрацию с хешированием пароля
    return {"message": "Registration endpoint - to be implemented"}

@app.post("/v1/login")
async def login():
    # TODO: Реализовать логин с JWT
    return {"message": "Login endpoint - to be implemented"}

@app.get("/v1/profile", response_model=UserResponse)
async def get_profile():
    # TODO: Реализовать получение профиля
    return {"message": "Profile endpoint - to be implemented"}

@app.put("/v1/profile", response_model=UserResponse)
async def update_profile():
    # TODO: Реализовать обновление профиля
    return {"message": "Update profile endpoint - to be implemented"}

@app.get("/v1/admin/users", response_model=list[UserResponse])
async def get_users_list():
    # TODO: Реализовать список пользователей для админа
    return {"message": "Admin users list endpoint - to be implemented"}