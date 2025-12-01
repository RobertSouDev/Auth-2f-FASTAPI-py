from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, func
from datetime import datetime, timedelta
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

# Funções para códigos de verificação
def create_verification_code(db: Session, email: str, code: str, code_hash: str, expires_at: datetime):
    """Cria um novo código de verificação."""
    db_code = models.VerificationCode(
        email=email,
        code=code,  # Código em texto plano
        code_hash=code_hash,
        expires_at=expires_at,
        status=models.CodeStatus.PENDENTE
    
    )
    db.add(db_code)
    db.commit()
    db.refresh(db_code)
    print(f"Código de verificação criado: {db_code.code_hash}")
    return db_code

def get_pending_code_by_email(db: Session, email: str):
    """Busca código pendente para um email."""
    return db.query(models.VerificationCode).filter(
        and_(
            models.VerificationCode.email == email,
            models.VerificationCode.status == models.CodeStatus.PENDENTE,
            models.VerificationCode.expires_at > datetime.utcnow()
        )
    ).order_by(models.VerificationCode.created_at.desc()).first()

def invalidate_previous_codes(db: Session, email: str):
    """Invalida todos os códigos pendentes anteriores para um email."""
    db.query(models.VerificationCode).filter(
        and_(
            models.VerificationCode.email == email,
            models.VerificationCode.status == models.CodeStatus.PENDENTE
        )
    ).update({"status": models.CodeStatus.CANCELADO})
    db.commit()

def update_code_status(db: Session, code_id: int, status: models.CodeStatus):
    """Atualiza o status de um código."""
    db_code = db.query(models.VerificationCode).filter(models.VerificationCode.id == code_id).first()
    if db_code:
        db_code.status = status
        db.commit()
        db.refresh(db_code)
    return db_code

def increment_code_attempts(db: Session, code_id: int):
    """Incrementa o contador de tentativas de um código."""
    db_code = db.query(models.VerificationCode).filter(models.VerificationCode.id == code_id).first()
    if db_code:
        db_code.attempts += 1
        db.commit()
        db.refresh(db_code)
    return db_code

def block_code(db: Session, code_id: int, blocked_until: datetime):
    """Bloqueia um código até uma data específica."""
    db_code = db.query(models.VerificationCode).filter(models.VerificationCode.id == code_id).first()
    if db_code:
        db_code.blocked_until = blocked_until
        db.commit()
        db.refresh(db_code)
    return db_code

# Funções para logs
def create_code_request_log(db: Session, email: str, ip_address: str = None, user_agent: str = None):
    """Cria um log de solicitação de código."""
    db_log = models.CodeRequestLog(
        email=email,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def create_code_validation_log(db: Session, email: str, code_id: int = None, success: bool = False, 
                               ip_address: str = None, user_agent: str = None):
    """Cria um log de validação de código."""
    db_log = models.CodeValidationLog(
        email=email,
        code_id=code_id,
        success=success,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def count_recent_requests(db: Session, email: str, minutes: int = 60):
    """Conta solicitações recentes de um email."""
    since = datetime.utcnow() - timedelta(minutes=minutes)
    return db.query(models.CodeRequestLog).filter(
        and_(
            models.CodeRequestLog.email == email,
            models.CodeRequestLog.created_at >= since
        )
    ).count()

# Funções para sessões
def create_email_session(db: Session, email: str, token: str, expires_at: datetime):
    """Cria uma nova sessão de email."""
    db_session = models.EmailSession(
        email=email,
        token=token,
        expires_at=expires_at,
        is_active=True
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_active_session_by_token(db: Session, token: str):
    """Busca uma sessão ativa pelo token."""
    return db.query(models.EmailSession).filter(
        and_(
            models.EmailSession.token == token,
            models.EmailSession.is_active == True,
            models.EmailSession.expires_at > datetime.utcnow()
        )
    ).first()

