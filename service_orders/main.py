import sys
import os
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import Optional
import uuid

from database_config import get_db, engine
from database import Order, Base
from schemas import OrderCreate, OrderResponse, OrderUpdate, OrderListResponse
from dependencies import (
    get_current_user_id, 
    get_order_with_permission, 
    get_current_user_id_and_roles, 
    require_manager_or_admin,
    get_all_orders_access
)
from utils import calculate_total_amount, validate_order_status_transition

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Orders Service", 
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "Orders service is running"}

@app.post("/v1/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    total_amount = calculate_total_amount(order_data.items)
    
    order = Order(
        user_id=current_user_id,
        items=[item.dict() for item in order_data.items],
        total_amount=total_amount,
        status="created"
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return order

@app.get("/v1/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order: Order = Depends(get_order_with_permission)
):
    return order

@app.get("/v1/orders", response_model=OrderListResponse)
async def get_orders_list(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    user_info: dict = Depends(get_current_user_id_and_roles),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None)
):
    user_roles = user_info["roles"]
    

    if "manager" in user_roles or "admin" in user_roles:
        query = db.query(Order)
    else:
        query = db.query(Order).filter(Order.user_id == current_user_id)
    
    if status:
        query = query.filter(Order.status == status)
    
    total = query.count()
    offset = (page - 1) * limit
    orders = query.offset(offset).limit(limit).all()
    
    pages = (total + limit - 1) // limit
    
    return OrderListResponse(
        orders=orders,
        total=total,
        page=page,
        pages=pages
    )

@app.patch("/v1/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    status_data: OrderUpdate,
    order: Order = Depends(get_order_with_permission), 
    user_info: dict = Depends(require_manager_or_admin), 
    db: Session = Depends(get_db)
):
    """Обновление статуса заказа - только для менеджеров и админов"""
    if not status_data.status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status is required"
        )
    
    if not validate_order_status_transition(order.status, status_data.status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot change status from {order.status} to {status_data.status}"
        )
    
    order.status = status_data.status
    db.commit()
    db.refresh(order)
    
    return order

@app.patch("/v1/orders/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order: Order = Depends(get_order_with_permission),
    user_info: dict = Depends(get_current_user_id_and_roles),
    db: Session = Depends(get_db)
):
    """Отмена заказа - инженер может отменить только свой заказ, менеджер/админ - любой"""
    user_roles = user_info["roles"]
    user_id = user_info["user_id"]
    
    if "engineer" in user_roles and "manager" not in user_roles and "admin" not in user_roles:
        if order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own orders"
            )
        if order.status != 'created':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Engineers can only cancel orders with 'created' status"
            )
    
    elif "manager" in user_roles or "admin" in user_roles:
        if order.status not in ['created', 'in_progress']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel order with status {order.status}"
            )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - engineer, manager or admin role required"
        )
    
    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    
    return order