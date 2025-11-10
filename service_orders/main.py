from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

app = FastAPI()

class Order(BaseModel):
    id: int
    userId: Optional[int] = None
    # ... другие поля заказа при необходимости ...

class OrderCreate(BaseModel):
    userId: Optional[int] = None
    # ... другие поля заказа при необходимости ...

fake_orders_db: Dict[int, Order] = {}
current_id = 1

@app.get('/orders/status')
def orders_status():
    return {"status": "Orders service is running"}

@app.get('/orders/health')
def orders_health():
    return {
        "status": "OK",
        "service": "Orders Service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get('/orders/{order_id}', response_model=Order)
def get_order(order_id: int):
    order = fake_orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get('/orders', response_model=List[Order])
def get_orders(userId: Optional[int] = Query(None)):
    orders = list(fake_orders_db.values())
    if userId is not None:
        orders = [order for order in orders if order.userId == userId]
    return orders

@app.post('/orders', response_model=Order, status_code=201)
def create_order(order: OrderCreate):
    global current_id
    order_obj = Order(id=current_id, **order.dict())
    fake_orders_db[current_id] = order_obj
    current_id += 1
    return order_obj

@app.put('/orders/{order_id}', response_model=Order)
def update_order(order_id: int, order_data: OrderCreate):
    if order_id not in fake_orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    updated = fake_orders_db[order_id].copy(update=order_data.dict(exclude_unset=True))
    fake_orders_db[order_id] = updated
    return updated

@app.delete('/orders/{order_id}')
def delete_order(order_id: int):
    if order_id not in fake_orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    deleted_order = fake_orders_db.pop(order_id)
    return {"message": "Order deleted", "deletedOrder": deleted_order}
