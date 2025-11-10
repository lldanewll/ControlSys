from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

app = FastAPI()

class User(BaseModel):
    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    # Добавьте другие поля пользователя, если есть.

class UserCreate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

fake_users_db: Dict[int, User] = {}
current_id = 1

@app.get("/users", response_model=List[User])
def get_users():
    return list(fake_users_db.values())

@app.post("/users", response_model=User, status_code=201)
def create_user(user: UserCreate):
    global current_id
    user_obj = User(id=current_id, **user.dict())
    fake_users_db[current_id] = user_obj
    current_id += 1
    return user_obj

@app.get("/users/health")
def users_health():
    return {
        "status": "OK",
        "service": "Users Service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/users/status")
def users_status():
    return {"status": "Users service is running"}

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    user = fake_users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, updates: UserCreate):
    user = fake_users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user = user.copy(update=updates.dict(exclude_unset=True))
    fake_users_db[user_id] = updated_user
    return updated_user

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    user = fake_users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    deleted_user = fake_users_db.pop(user_id)
    return {"message": "User deleted", "deletedUser": deleted_user}
