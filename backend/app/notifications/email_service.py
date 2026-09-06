"""
Email delivery via stdlib smtplib (no extra dependency, per requirements.txt
note). Every public function here is safe to call unconditionally from
request-handling code: if EMAIL_ENABLED is false, EMAIL_PASSWORD is empty,
or the SMTP server is unreachable, the failure is logged and swallowed —
it NEVER raises, so a flaky mail server can't break complaint submission
or status updates. This mirrors the AI fallback philosophy from Part 2:
degrade gracefully, never crash.
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger("smartcivicai.email")


def send_email(to_email: str, subject: str, html_body: str, text_body: str | None = None) -> bool:
    """Returns True if the email was actually sent, False otherwise (never raises)."""
    if not settings.EMAIL_ENABLED:
        logger.info("Email disabled (EMAIL_ENABLED=false) — skipping send to %s: %s", to_email, subject)
        return False
    if not settings.EMAIL_PASSWORD:
        logger.info("No EMAIL_PASSWORD configured — skipping send to %s: %s", to_email, subject)
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.APP_EMAIL
    message["To"] = to_email
    message.attach(MIMEText(text_body or _strip_html(html_body), "plain"))
    message.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(settings.APP_EMAIL, settings.EMAIL_PASSWORD)
            server.sendmail(settings.APP_EMAIL, [to_email], message.as_string())
        logger.info("Email sent to %s: %s", to_email, subject)
        return True
    except Exception:
        logger.exception("Failed to send email to %s (subject: %s) — continuing without it", to_email, subject)
        return False


def _strip_html(html: str) -> str:
    import re

    return re.sub(r"<[^>]+>", "", html).strip()


# --------------------------------------------------------------------------
# Templated notifications
# --------------------------------------------------------------------------

_EMAIL_WRAPPER = """
<div style="font-family: sans-serif; max-width: 560px; margin: 0 auto; color: #1B2A4A;">
  <div style="background: #1B2A4A; color: #F3F4EF; padding: 16px 24px;">
    <strong style="font-size: 18px;">SmartCivicAI</strong>
  </div>
  <div style="padding: 24px; border: 1px solid #eee; border-top: none;">
    {content}
  </div>
  <p style="color: #7C86A0; font-size: 12px; padding: 0 24px;">
    This is an automated message from the SmartCivicAI complaint management platform.
  </p>
</div>
"""


def send_new_complaint_admin_email(*, complaint, department_name: str | None, citizen_email: str, view_url: str) -> bool:
    """spec §13: sent to ADMIN_EMAIL from APP_EMAIL whenever a new complaint is registered."""
    rows = "".join(
        f'<tr><td style="padding:4px 8px; color:#7C86A0;">{label}</td>'
        f'<td style="padding:4px 8px;">{value}</td></tr>'
        for label, value in [
            ("Complaint ID", complaint.complaint_number),
            ("Module", complaint.module.value.replace("_", " ")),
            ("Category", complaint.category.name_en if complaint.category else "—"),
            ("Summary", complaint.summary or complaint.original_text[:200]),
            ("Language", complaint.original_language.value.upper()),
            ("Priority", complaint.priority.value),
            ("Status", complaint.status.value),
            ("Location", complaint.address or f"{complaint.latitude}, {complaint.longitude}" if complaint.latitude else "Not provided"),
            ("Date/time", complaint.created_at.strftime("%Y-%m-%d %H:%M UTC")),
            ("Citizen", citizen_email),
            ("AI classification", f"module confidence set by demo AI pipeline" if complaint.ai_analysis else "pending"),
            ("Assigned department", department_name or "Not yet routed"),
        ]
    )
    content = f"""
    <h2 style="margin-top:0;">New complaint registered</h2>
    <table style="border-collapse: collapse; font-size: 14px;">{rows}</table>
    <p style="margin-top: 20px;">
      <a href="{view_url}" style="background:#E8A33D; color:#1B2A4A; padding:10px 18px; text-decoration:none; font-weight:600;">
        View complaint
      </a>
    </p>
    """
    return send_email(
        settings.ADMIN_EMAIL,
        f"[SmartCivicAI] New complaint {complaint.complaint_number} — {complaint.priority.value} priority",
        _EMAIL_WRAPPER.format(content=content),
    )


_STATUS_CHANGE_SUBJECTS = {
    "en": "Your complaint {number} status changed to {status}",
    "te": "మీ ఫిర్యాదు {number} స్థితి {status}కి మారింది",
    "hi": "आपकी शिकायत {number} की स्थिति {status} में बदल गई",
}
_STATUS_CHANGE_BODIES = {
    "en": "<p>Your complaint <strong>{number}</strong> is now <strong>{status}</strong>.</p><p>{note}</p>",
    "te": "<p>మీ ఫిర్యాదు <strong>{number}</strong> ఇప్పుడు <strong>{status}</strong>గా ఉంది.</p><p>{note}</p>",
    "hi": "<p>आपकी शिकायत <strong>{number}</strong> अब <strong>{status}</strong> है।</p><p>{note}</p>",
}


def send_status_change_email(*, complaint, citizen_email: str, language: str, note: str | None, view_url: str) -> bool:
    lang = language if language in _STATUS_CHANGE_SUBJECTS else "en"
    subject = _STATUS_CHANGE_SUBJECTS[lang].format(number=complaint.complaint_number, status=complaint.status.value)
    body = _STATUS_CHANGE_BODIES[lang].format(number=complaint.complaint_number, status=complaint.status.value, note=note or "")
    content = f"{body}<p><a href='{view_url}'>View complaint</a></p>"
    return send_email(citizen_email, subject, _EMAIL_WRAPPER.format(content=content))


def send_complaint_assigned_email(*, complaint, officer_email: str, view_url: str) -> bool:
    content = f"""
    <h2 style="margin-top:0;">New complaint assigned to you</h2>
    <p>Complaint <strong>{complaint.complaint_number}</strong> ({complaint.module.value.replace('_', ' ')},
    priority: {complaint.priority.value}) has been assigned to you.</p>
    <p><a href="{view_url}">View and act on this complaint</a></p>
    """
    return send_email(
        officer_email, f"[SmartCivicAI] Complaint {complaint.complaint_number} assigned to you",
        _EMAIL_WRAPPER.format(content=content),
    )
