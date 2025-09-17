import logging
from typing import Optional
from urllib.parse import urlencode
from aiosmtplib import SMTP
from email.message import EmailMessage
from app.core.config.settings import settings

log = logging.getLogger(__name__)

class EmailSender:
    async def send(self, to: str, subject: str, html: str, text: Optional[str] = None):
        raise NotImplementedError

class ConsoleEmailSender(EmailSender):
    async def send(self, to: str, subject: str, html: str, text: Optional[str] = None):
        log.info("=== DEV EMAIL ===\nTo: %s\nSubject: %s\nText: %s\nHTML:\n%s\n=== /DEV EMAIL ===", to, subject, text or "", html)

class SmtpEmailSender(EmailSender):
    async def send(self, to: str, subject: str, html: str, text: Optional[str] = None):
        msg = EmailMessage()
        msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
        msg["To"] = to
        msg["Subject"] = subject
        if text:
            msg.set_content(text)
            msg.add_alternative(html, subtype="html")
        else:
            msg.set_content(html, subtype="html")

        async with SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=False,
            start_tls=settings.SMTP_TLS,
        ) as smtp:
            if settings.SMTP_USER and settings.SMTP_PASS:
                await smtp.login(settings.SMTP_USER, settings.SMTP_PASS)
            await smtp.send_message(msg)

def get_email_sender() -> EmailSender:
    # If SMTP_HOST missing, use console sender
    if not settings.SMTP_HOST:
        return ConsoleEmailSender()
    return SmtpEmailSender()

def build_frontend_link(path: str, token: str) -> str:
    base = settings.FRONTEND_URL.rstrip("/")
    p = path if path.startswith("/") else f"/{path}"
    qs = urlencode({"token": token})
    return f"{base}{p}?{qs}"
