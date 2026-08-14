"""Email service for sending outreach emails via SMTP - standalone module."""
from __future__ import annotations

import logging
import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

logger = logging.getLogger(__name__)

SMTP_HOST = "sapphire.scnservers.net"
SMTP_PORT = 465
SMTP_EMAIL = "vansh@inowix.in"
SMTP_PASSWORD = "ANEzHAywQ7hyMvmzYC2u"
SMTP_USE_SSL = True


def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
    from_email: str = SMTP_EMAIL,
    from_name: str = "Vansh from Inowix",
    cc: str | list[str] | None = None,
    retries: int = 3,
    retry_backoff_sec: float = 8.0,
) -> dict[str, Any]:
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email
    msg["Subject"] = subject

    cc_list: list[str] = []
    if isinstance(cc, str) and cc.strip():
        cc_list = [p.strip() for p in cc.split(",") if p.strip()]
    elif isinstance(cc, list):
        cc_list = [str(p).strip() for p in cc if str(p).strip()]
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)

    if body_text:
        msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    recipients = [to_email, *cc_list]
    last_err: Exception | None = None

    for attempt in range(1, max(1, retries) + 1):
        try:
            if SMTP_USE_SSL:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
                    server.login(SMTP_EMAIL, SMTP_PASSWORD)
                    server.sendmail(from_email, recipients, msg.as_string())
            else:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                    server.starttls()
                    server.login(SMTP_EMAIL, SMTP_PASSWORD)
                    server.sendmail(from_email, recipients, msg.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return {"success": True, "to": to_email, "cc": cc_list, "subject": subject}
        except Exception as e:
            last_err = e
            logger.error(f"Failed to send email to {to_email} (attempt {attempt}): {e}")
            if attempt < retries:
                time.sleep(retry_backoff_sec * attempt)

    return {"success": False, "to": to_email, "error": str(last_err) if last_err else "unknown"}


def send_bulk_emails(
    recipients: list[dict[str, Any]],
    subject_template: str,
    body_template: str,
    from_email: str = SMTP_EMAIL,
    from_name: str = "Vansh from Inowix",
) -> dict[str, Any]:
    results = []
    success_count = 0
    fail_count = 0

    for recipient in recipients:
        subject = subject_template
        body = body_template

        for key, value in recipient.items():
            placeholder = "{" + key + "}"
            if placeholder in subject:
                subject = subject.replace(placeholder, str(value or ""))
            if placeholder in body:
                body = body.replace(placeholder, str(value or ""))

        result = send_email(
            to_email=recipient.get("email", ""),
            subject=subject,
            body_html=body,
            from_email=from_email,
            from_name=from_name,
        )

        results.append(result)
        if result["success"]:
            success_count += 1
        else:
            fail_count += 1

    return {
        "total": len(recipients),
        "success": success_count,
        "failed": fail_count,
        "results": results,
    }


def generate_outreach_email(
    company_name: str,
    problem: str | None = None,
    solution_match: str | None = None,
    founder_name: str | None = None,
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, str]:
    evidence_text = ""
    if evidence:
        evidence_items = []
        for ev in evidence[:3]:
            if isinstance(ev, dict):
                summary = ev.get("summary", ev.get("description", ""))
                if summary:
                    evidence_items.append(f"  - {summary}")
        if evidence_items:
            evidence_text = "\n\nWhat I noticed:\n" + "\n".join(evidence_items)

    greeting = f"Hi {founder_name}," if founder_name else "Hi there,"
    subject = f"Quick question about {company_name}'s {solution_match or 'growth'}"

    body = f"""{greeting}

I came across {company_name} and noticed you might be dealing with {problem or 'some challenges in your space'}.

{'I think our ' + solution_match + ' solution could help you tackle this.' if solution_match else 'I think we might be able to help.'}
{evidence_text}

Would you be open to a quick 15-minute chat this week to explore if there's a fit?

Best,
Vansh
Founder, Inowix
https://inowix.in

P.S. I only reach out when I see a genuine opportunity - no generic sales pitch here."""

    return {"subject": subject, "body": body}
