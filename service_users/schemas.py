from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str
    roles: List[str] = ["engineer"]
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v
    
    @validator('roles')
    def validate_roles(cls, v):
        valid_roles = ["engineer", "manager", "admin"]
        for role in v:
            if role not in valid_roles:
                raise ValueError(f'Role must be one of: {valid_roles}')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    roles: Optional[List[str]] = None

class UserResponse(UserBase):
    id: UUID
    roles: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"