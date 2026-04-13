"""Async email delivery via aiosmtplib with TLS and header injection prevention."""
import html
import logging
import re

import aiosmtplib

from shared.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
_HEADER_INJECTION_RE = re.compile(r"[\r\n]")


def validate_email(email: str) -> str:
    """Validate recipient email format. Raises ValueError if invalid."""
    email = email.strip()
    if not _EMAIL_RE.match(email):
        raise ValueError(f"Invalid email format: {email!r}")
    if _HEADER_INJECTION_RE.search(email):
        raise ValueError("Email contains header injection characters")
    return email


def sanitize_for_email(text: str) -> str:
    """Sanitize dynamic content for email body — prevent header injection and XSS."""
    text = _HEADER_INJECTION_RE.sub("", text)
    return html.escape(text)


def render_email_html(
    title: str,
    document_title: str,
    summary: str,
    urgency_level: str,
    rule_name: str,
    detail_url: str = "",
) -> str:
    """Render notification email HTML with inline CSS (no external resources)."""
    safe_title = sanitize_for_email(title)
    safe_doc_title = sanitize_for_email(document_title)
    safe_summary = sanitize_for_email(summary)
    safe_urgency = sanitize_for_email(urgency_level)
    safe_rule = sanitize_for_email(rule_name)
    safe_url = sanitize_for_email(detail_url)

    urgency_color = {
        "critical": "#e53e3e",
        "high": "#dd6b20",
        "normal": "#3182ce",
        "low": "#38a169",
    }.get(urgency_level, "#3182ce")

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f7fafc;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <div style="background: {urgency_color}; padding: 15px 20px; color: white;">
            <h2 style="margin: 0;">{safe_title}</h2>
        </div>
        <div style="padding: 20px;">
            <p style="color: #718096; margin-top: 0;">Triggered by rule: <strong>{safe_rule}</strong></p>
            <h3 style="color: #2d3748;">{safe_doc_title}</h3>
            <p style="color: #4a5568;">{safe_summary}</p>
            <p><span style="display: inline-block; background: {urgency_color}; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.85em;">Urgency: {safe_urgency}</span></p>
            {f'<p><a href="{safe_url}" style="color: #3182ce;">View Details</a></p>' if safe_url else ''}
        </div>
        <div style="padding: 15px 20px; background: #f7fafc; color: #a0aec0; font-size: 0.8em;">
            RegulatorAI Notification Service
        </div>
    </div>
</body>
</html>"""


async def send_email(
    to: str,
    subject: str,
    html_body: str,
    from_addr: str | None = None,
) -> bool:
    """Send email via SMTP with TLS."""
    to = validate_email(to)

    # Prevent header injection in subject
    safe_subject = _HEADER_INJECTION_RE.sub("", subject)

    from_addr = from_addr or settings.smtp_user or "noreply@regulatorai.com"

    if not settings.smtp_host:
        logger.warning("SMTP not configured, skipping email to %s", to)
        return False

    try:
        message = f"""From: {from_addr}\r\nTo: {to}\r\nSubject: {safe_subject}\r\nContent-Type: text/html; charset=UTF-8\r\nMIME-Version: 1.0\r\n\r\n{html_body}"""

        await aiosmtplib.send(
            message.encode("utf-8"),
            sender=from_addr,
            recipients=[to],
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user or None,
            password=settings.smtp_password or None,
            use_tls=True,
        )
        logger.info("Email sent to %s: %s", to, safe_subject)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        return False
