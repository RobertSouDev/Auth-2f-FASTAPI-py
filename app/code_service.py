import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional

def generate_code() -> str:
    """
    Gera um código numérico de 4 dígitos.
    """
    return f"{secrets.randbelow(10000):04d}"

def hash_code(code: str) -> str:
    """
    Gera hash SHA-256 do código para armazenamento seguro.
    """
    return hashlib.sha256(code.encode()).hexdigest()

def verify_code(plain_code: str, code_hash: str) -> bool:
    """
    Verifica se o código em texto plano corresponde ao hash armazenado.
    """
    computed_hash = hash_code(plain_code)
    return computed_hash == code_hash

def normalize_code(code: str) -> str:
    """
    Normaliza o código removendo espaços e convertendo para maiúsculas.
    Para códigos numéricos, apenas remove espaços.
    """
    return code.strip().replace(" ", "")

def get_code_expiration(minutes: int = 10) -> datetime:
    """
    Retorna a data/hora de expiração do código.
    Padrão: 10 minutos a partir de agora.
    """
    return datetime.utcnow() + timedelta(minutes=minutes)

def is_code_expired(expires_at: datetime) -> bool:
    """
    Verifica se o código expirou.
    """
    return datetime.utcnow() > expires_at

def get_block_duration(minutes: int = 60) -> datetime:
    """
    Retorna a data/hora até quando o email estará bloqueado.
    Padrão: 1 hora a partir de agora.
    """
    return datetime.utcnow() + timedelta(minutes=minutes)

def is_blocked(blocked_until: Optional[datetime]) -> bool:
    """
    Verifica se o email está bloqueado.
    """
    if blocked_until is None:
        return False
    return datetime.utcnow() < blocked_until

