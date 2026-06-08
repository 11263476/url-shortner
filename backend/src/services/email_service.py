import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.core.config import settings
from src.logging import get_logger


class EmailService:
    SMTP_HOST: str = settings.SMTP_HOST
    SMTP_PORT: int = settings.SMTP_PORT
    SMTP_USER: str = settings.SMTP_USER
    SMTP_PASSWORD: str = settings.SMTP_PASSWORD
    FROM_EMAIL: str = settings.FROM_EMAIL
    FROM_NAME: str = settings.FROM_NAME

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.SMTP_HOST and cls.SMTP_USER and cls.SMTP_PASSWORD)

    @classmethod
    async def send_verification_email(cls, email: str, token: str) -> None:
        verify_url = f"{settings.FRONTEND_URL or 'http://localhost:3000'}/verify-email?token={token}"
        subject = "Verify your email — LinkForge"
        html = f"""
        <h2>Welcome to LinkForge!</h2>
        <p>Click the link below to verify your email address:</p>
        <p><a href="{verify_url}">{verify_url}</a></p>
        <p>This link expires in 24 hours.</p>
        """
        await cls._send(email, subject, html)

    @classmethod
    async def send_password_reset(cls, email: str, token: str) -> None:
        reset_url = f"{settings.FRONTEND_URL or 'http://localhost:3000'}/reset-password?token={token}"
        subject = "Reset your password — LinkForge"
        html = f"""
        <h2>Password Reset Request</h2>
        <p>Click the link below to reset your password:</p>
        <p><a href="{reset_url}">{reset_url}</a></p>
        <p>This link expires in 1 hour.</p>
        <p>If you didn't request this, you can safely ignore this email.</p>
        """
        await cls._send(email, subject, html)

    @classmethod
    async def _send(cls, to_email: str, subject: str, html: str) -> None:
        logger = get_logger("email")
        if not cls.is_configured():
            logger.info(f"[EMAIL] Would send email to {to_email}: {subject}")
            return
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{cls.FROM_NAME} <{cls.FROM_EMAIL}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(html, "html"))
            with smtplib.SMTP(cls.SMTP_HOST, cls.SMTP_PORT) as server:
                server.starttls()
                server.login(cls.SMTP_USER, cls.SMTP_PASSWORD)
                server.sendmail(cls.FROM_EMAIL, [to_email], msg.as_string())
            logger.info(f"Email sent to {to_email}: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
