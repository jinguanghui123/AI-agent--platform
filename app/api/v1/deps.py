from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

async def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db

async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    return user