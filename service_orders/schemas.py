from pydantic import BaseModel, validator
from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class OrderItem(BaseModel):
    product: str
    quantity: int
    price: Decimal
    
    @validator('quantity')
    def quantity_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v

class OrderBase(BaseModel):
    items: List[OrderItem]
    total_amount: Decimal

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v and v not in ['created', 'in_progress', 'completed', 'cancelled']:
            raise ValueError('Status must be: created, in_progress, completed, cancelled')
        return v

class OrderResponse(OrderBase):
    id: UUID
    user_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    pages: int