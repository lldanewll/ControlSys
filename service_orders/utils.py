from decimal import Decimal
from typing import List
from schemas import OrderItem

def calculate_total_amount(items: List[OrderItem]) -> float:
    """Рассчитывает общую сумму заказа"""
    total = 0.0
    for item in items:
        total += item.price * item.quantity
    return total

def validate_order_status_transition(current_status: str, new_status: str) -> bool:
    """Проверяет допустимость перехода статусов"""
    valid_transitions = {
        'created': ['in_progress', 'cancelled'],
        'in_progress': ['completed', 'cancelled'],
        'completed': [],
        'cancelled': []
    }
    
    return new_status in valid_transitions.get(current_status, [])  