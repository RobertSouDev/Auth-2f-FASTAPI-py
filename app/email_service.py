import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Configurações de email
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Sistema de Autenticação")

def create_email_template(code: str) -> str:
    """
    Cria o template HTML do email com o código de verificação.
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .code-box {{
                background-color: #f4f4f4;
                border: 2px solid #333;
                border-radius: 5px;
                padding: 20px;
                text-align: center;
                font-size: 32px;
                font-weight: bold;
                letter-spacing: 5px;
                margin: 20px 0;
            }}
            .footer {{
                margin-top: 30px;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Código de Verificação</h1>
            <p>Olá,</p>
            <p>Você solicitou um código de verificação para fazer login. Use o código abaixo:</p>
            <div class="code-box">{code}</div>
            <p>Este código é válido por 10 minutos.</p>
            <p>Se você não solicitou este código, ignore este email.</p>
            <div class="footer">
                <p>Este é um email automático, por favor não responda.</p>
            </div>
        </div>
    </body>
    </html>
    """

def send_verification_code(email: str, code: str) -> bool:
    """
    Envia o código de verificação por email.
    
    NOTA: Envio de email está DESATIVADO.
    Esta função apenas registra o código gerado no log.
    
    Args:
        email: Email do destinatário
        code: Código de verificação a ser enviado
        
    Returns:
        True se o email foi enviado com sucesso, False caso contrário
    """
    # Envio de email desativado - apenas loga o código gerado
    logger.info("=" * 60)
    logger.info("EMAIL DESATIVADO - CÓDIGO DE VERIFICAÇÃO GERADO")
    logger.info(f"Email: {email}")
    logger.info(f"Código: {code}")
    logger.info("=" * 60)
    return True  # Retorna True para não quebrar o fluxo da aplicação
    
    # Código original de envio de email comentado abaixo:
    """
    try:
        # Criar mensagem
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Código de Verificação"
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg["To"] = email
        
        # Criar conteúdo HTML
        html_content = create_email_template(code)
        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)
        
        # Enviar email
        if not SMTP_USER or not SMTP_PASSWORD:
            logger.error("SMTP credentials not configured. Email cannot be sent.")
            logger.error(f"Código gerado: {code} para {email} (email NÃO foi enviado)")
            return False  # Retorna False quando não pode enviar
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Verification code sent successfully to {email}")
        return True
        
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email to {email}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email to {email}: {str(e)}", exc_info=True)
        return False
    """
