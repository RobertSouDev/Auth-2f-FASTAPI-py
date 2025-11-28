from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import timedelta
import uvicorn
import logging

from . import models, schemas, crud, auth
from .database import get_db, engine

logger = logging.getLogger(__name__)


models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Authentication System", version="1.0.0")
security = HTTPBearer()

@app.get("/")
def read_root():
    return "Hello World"

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        # Verificar se o username já existe
        db_user = crud.get_user_by_username(db, username=user.username)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Verificar se o email já existe
        db_user = crud.get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Criar o usuário
        new_user = crud.create_user(db=db, user=user)
        return new_user
    
    except HTTPException:
        # Re-raise HTTPExceptions (já tratadas)
        raise
    except ValueError as e:
        # Erro de validação do CRUD (ex: usuário já existe)
        db.rollback()
        logger.error(f"Validation error during user registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except IntegrityError as e:
        # Erro de integridade do banco de dados (ex: constraint violation)
        db.rollback()
        logger.error(f"Integrity error during user registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User registration failed due to database constraint violation"
        )
    except Exception as e:
        # Qualquer outro erro inesperado
        db.rollback()
        logger.error(f"Unexpected error during user registration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while registering the user"
        )

@app.post("/login", response_model=schemas.Token)
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    username = auth.verify_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user



