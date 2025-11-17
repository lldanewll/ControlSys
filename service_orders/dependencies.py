from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database_config import get_db
from database import Order
from auth import get_token_payload
import uuid
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_user_id_and_roles(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """Зависимость для получения user_id и ролей из JWT"""
    payload = get_token_payload(credentials.credentials)
    
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    user_id_str = payload.get("sub")
    try:
        user_id = uuid.UUID(user_id_str)
        
        # Получаем роли из JWT payload
        user_roles = payload.get("roles", ["engineer"])
        
        return {"user_id": user_id, "roles": user_roles}
        
    except ValueError as e:
        logger.error(f"Invalid UUID format: {user_id_str}, error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
        )

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> uuid.UUID:
    """Зависимость для получения только user_id из JWT"""
    user_info = await get_current_user_id_and_roles(credentials, db)
    return user_info["user_id"]

async def get_order_with_permission(
    order_id: uuid.UUID,
    user_info: dict = Depends(get_current_user_id_and_roles),
    db: Session = Depends(get_db)
) -> Order:
    """Проверяет права доступа к заказу - менеджеры и админы имеют доступ ко всем заказам"""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    user_id = user_info["user_id"]
    user_roles = user_info["roles"]
    
    # Менеджеры и админы имеют доступ ко всем заказам
    if "manager" in user_roles or "admin" in user_roles:
        return order
    
    # Инженеры имеют доступ только к своим заказам
    if order.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this order"
        )
    
    return order

async def require_manager_or_admin(user_info: dict = Depends(get_current_user_id_and_roles)):
    """Проверяет что пользователь менеджер или админ"""
    user_roles = user_info["roles"]
    if "manager" not in user_roles and "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or admin role required"
        )
    return user_info

async def get_all_orders_access(user_info: dict = Depends(get_current_user_id_and_roles)):
    """Проверяет права на доступ ко всем заказам (для менеджеров и админов)"""
    user_roles = user_info["roles"]
    if "manager" not in user_roles and "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or admin role required to access all orders"
        )
    return user_info