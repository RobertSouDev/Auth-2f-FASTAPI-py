from fastapi import FastAPI, Depends, HTTPException, status, Form
from starlette.requests import Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import timedelta, datetime
import uvicorn
import logging

from . import models, schemas, crud, auth
from .database import get_db, engine
from . import code_service, email_service

# Configurar logging para exibir no console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

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

# Configurações
MAX_REQUESTS_PER_HOUR = 3
CODE_VALIDITY_MINUTES = 10
MAX_VALIDATION_ATTEMPTS = 3
BLOCK_DURATION_MINUTES = 60

@app.post("/api/solicitar-codigo", response_model=schemas.CodeResponse)
def solicitar_codigo(request: schemas.CodeRequest, db: Session = Depends(get_db), 
                    http_request: Request = None):
    """
    Solicita um código de verificação por email.
    """
    try:
        email = request.email.lower().strip()
        
        # 1. Valida formato do email (já validado pelo Pydantic)
        
        # 2. Verifica se não há muitas solicitações recentes (rate limiting)
        recent_requests = crud.count_recent_requests(db, email, minutes=60)
        if recent_requests >= MAX_REQUESTS_PER_HOUR:
            logger.warning(f"Rate limit exceeded for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas solicitações. Tente novamente em 1 hora."
            )
        
        # 3. Gera código único
        code = code_service.generate_code()
        code_hash = code_service.hash_code(code)
        
        # 4. Define expiração
        expires_at = code_service.get_code_expiration(CODE_VALIDITY_MINUTES)
        
        # 5. Invalida códigos anteriores pendentes
        crud.invalidate_previous_codes(db, email)
        
        # 6. Armazena código + email + timestamp
        db_code = crud.create_verification_code(db, email, code, code_hash, expires_at)
        
        # 7. Registra no log
        ip_address = http_request.client.host if http_request else None
        user_agent = http_request.headers.get("user-agent") if http_request else None
        crud.create_code_request_log(db, email, ip_address, user_agent)
        
        # 8. Envia email com o código
        email_sent = email_service.send_verification_code(email, code)
        if not email_sent:
            logger.error(f"Failed to send email to {email}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Código gerado com sucesso, mas não foi possível enviar o email. Verifique a configuração do servidor de email."
            )
        
        logger.info(f"Verification code requested and sent successfully to {email}")
        
        return schemas.CodeResponse(message="Código enviado para seu email")
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error requesting code: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao solicitar código de verificação"
        )

@app.post("/api/validar-codigo", response_model=schemas.ValidationResponse)
def validar_codigo(request: schemas.CodeValidation, db: Session = Depends(get_db),
                  http_request: Request = None):
    """
    Valida o código de verificação e retorna token de acesso.
    """
    try:
        email = request.email.lower().strip()
        code = code_service.normalize_code(request.code)
        
        # 1. Busca código pendente para aquele email
        db_code = crud.get_pending_code_by_email(db, email)
        
        if not db_code:
            # Registra tentativa falha
            ip_address = http_request.client.host if http_request else None
            user_agent = http_request.headers.get("user-agent") if http_request else None
            crud.create_code_validation_log(db, email, None, False, ip_address, user_agent)
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Código não encontrado ou já utilizado"
            )
        
        # 2. Verifica se código não expirou
        if code_service.is_code_expired(db_code.expires_at):
            crud.update_code_status(db, db_code.id, models.CodeStatus.EXPIRADO)
            
            ip_address = http_request.client.host if http_request else None
            user_agent = http_request.headers.get("user-agent") if http_request else None
            crud.create_code_validation_log(db, email, db_code.id, False, ip_address, user_agent)
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código expirado"
            )
        
        # 3. Verifica se código não foi usado
        if db_code.status != models.CodeStatus.PENDENTE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código já foi utilizado"
            )
        
        # 4. Verifica se não excedeu tentativas
        if db_code.attempts >= MAX_VALIDATION_ATTEMPTS:
            # Bloqueia o código
            blocked_until = code_service.get_block_duration(BLOCK_DURATION_MINUTES)
            crud.block_code(db, db_code.id, blocked_until)
            
            ip_address = http_request.client.host if http_request else None
            user_agent = http_request.headers.get("user-agent") if http_request else None
            crud.create_code_validation_log(db, email, db_code.id, False, ip_address, user_agent)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas. Tente novamente em 1 hora."
            )
        
        # 5. Verifica se está bloqueado
        if code_service.is_blocked(db_code.blocked_until):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Código bloqueado. Tente novamente mais tarde."
            )
        
        # 6. Compara código recebido com código armazenado
        if not code_service.verify_code(code, db_code.code_hash):
            # Incrementa contador de tentativas
            crud.increment_code_attempts(db, db_code.id)
            
            # Registra tentativa falha
            ip_address = http_request.client.host if http_request else None
            user_agent = http_request.headers.get("user-agent") if http_request else None
            crud.create_code_validation_log(db, email, db_code.id, False, ip_address, user_agent)
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código inválido"
            )
        
        # 7. Se correto: marca como usado, cria sessão de acesso
        crud.update_code_status(db, db_code.id, models.CodeStatus.VALIDADO)
        
        # Busca ou cria usuário (se não existir, pode criar um novo usuário)
        user = crud.get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado. Por favor, registre-se primeiro."
            )
        
        # Cria token de acesso
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        # Cria sessão de email
        session_expires_at = datetime.utcnow() + access_token_expires
        crud.create_email_session(db, email, access_token, session_expires_at)
        
        # Registra validação bem-sucedida
        ip_address = http_request.client.host if http_request else None
        user_agent = http_request.headers.get("user-agent") if http_request else None
        crud.create_code_validation_log(db, email, db_code.id, True, ip_address, user_agent)
        
        logger.info(f"Code validated successfully for email: {email}")
        
        return schemas.ValidationResponse(
            access_token=access_token,
            token_type="bearer",
            user=schemas.UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error validating code: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao validar código"
        )

@app.post("/api/reenviar-codigo", response_model=schemas.CodeResponse)
def reenviar_codigo(request: schemas.ReenviarCodigoRequest, db: Session = Depends(get_db),
                   http_request: Request = None):
    """
    Reenvia um novo código de verificação, invalidando o anterior.
    """
    try:
        email = request.email.lower().strip()
        
        # 1. Verifica rate limiting
        recent_requests = crud.count_recent_requests(db, email, minutes=60)
        if recent_requests >= MAX_REQUESTS_PER_HOUR:
            logger.warning(f"Rate limit exceeded for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas solicitações. Tente novamente em 1 hora."
            )
        
        # 2. Invalida código anterior (se existir)
        crud.invalidate_previous_codes(db, email)
        
        # 3. Segue mesmo fluxo do endpoint de solicitação
        code = code_service.generate_code()
        code_hash = code_service.hash_code(code)
        expires_at = code_service.get_code_expiration(CODE_VALIDITY_MINUTES)
        
        db_code = crud.create_verification_code(db, email, code, code_hash, expires_at)
        
        # Registra no log
        ip_address = http_request.client.host if http_request else None
        user_agent = http_request.headers.get("user-agent") if http_request else None
        crud.create_code_request_log(db, email, ip_address, user_agent)
        
        # Envia email
        email_sent = email_service.send_verification_code(email, code)
        if not email_sent:
            logger.error(f"Failed to send email to {email}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Código gerado com sucesso, mas não foi possível enviar o email. Verifique a configuração do servidor de email."
            )
        
        logger.info(f"Verification code resent successfully to {email}")
        
        return schemas.CodeResponse(message="Código reenviado para seu email")
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error resending code: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao reenviar código de verificação"
        )



