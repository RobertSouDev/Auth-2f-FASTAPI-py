from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from . import models, schemas, auth
import logging

logger = logging.getLogger(__name__)

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate):
    try:
        hashed_password = auth.get_password_hash(user.password)
        db_user = models.User(
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating user: {str(e)}")
        # Verificar qual constraint foi violada
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        if "email" in error_msg.lower() or "unique constraint" in error_msg.lower():
            raise ValueError("Email already registered")
        elif "username" in error_msg.lower():
            raise ValueError("Username already registered")
        else:
            raise ValueError("User registration failed due to database constraint")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating user: {str(e)}", exc_info=True)
        raise

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        user = get_user_by_email(db, username)
    if not user:
        return False
    if not auth.verify_password(password, user.hashed_password):
        return False
    return user

