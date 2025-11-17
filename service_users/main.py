import sys
import os
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from database_config import get_db
from database import User
from schemas import UserCreate, UserResponse, UserUpdate, UserLogin, Token
from utils import hash_password, verify_password
from auth import create_access_token
from dependencies import get_current_user, require_roles

@asynccontextmanager
async def lifespan(app: FastAPI):
    from database_config import engine
    from database import Base
    Base.metadata.create_all(bind=engine)
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
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    hashed_password = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
        roles=user_data.roles
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@app.post("/v1/login", response_model=Token)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(data={
        "sub": str(user.id),
        "roles": user.roles
    })
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/v1/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@app.put("/v1/profile", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@app.get("/v1/admin/users", response_model=list[UserResponse])
async def get_users_list(
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return users

@app.post("/v1/admin/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    user_data: UserCreate,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    """Создание пользователя админом (с любыми ролями)"""
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    hashed_password = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
        roles=user_data.roles
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user