from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database_config import get_db
from .database import Order, User
import uuid

security = HTTPBearer()

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> uuid.UUID:
    """Извлекает user_id из JWT токена"""
    # В реальном проекте здесь был бы вызов сервиса пользователей
    # Пока используем заглушку - первый пользователь из БД
    return uuid.uuid4()

async def get_order_with_permission(
    order_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> Order:
    """Проверяет права доступа к заказу"""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Проверяем что пользователь имеет доступ к заказу
    if order.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this order"
        )
    
    return order