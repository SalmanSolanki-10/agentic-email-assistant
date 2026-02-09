from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple

log = logging.getLogger(__name__)


class EmailResponder:
    """Sends replies via SMTP. If not configured, runs in demo mode."""

    def __init__(self, smtp_user: str = "", smtp_app_password: str = "", cpa_name: str = "John Martinez"):
        self.smtp_user = smtp_user
        self.smtp_app_password = smtp_app_password
        self.cpa_name = cpa_name
        self.enabled = bool(smtp_user and smtp_app_password)

    def configure(self, smtp_user: str, smtp_app_password: str, cpa_name: str) -> None:
        self.smtp_user = smtp_user
        self.smtp_app_password = smtp_app_password
        self.cpa_name = cpa_name
        self.enabled = bool(smtp_user and smtp_app_password)
        log.info("Email responder configured for %s", smtp_user)

    def send_response(
        self,
        smtp_host: str,
        smtp_port: int,
        to_email: str,
        original_subject: str,
        response_content: str,
    ) -> Tuple[bool, str]:
        if not self.enabled:
            log.info("[DEMO MODE] Would send response to %s (subject=%s)", to_email, original_subject)
            return True, f"Demo mode: response logged for {to_email}"

        msg = MIMEMultipart()
        msg["From"] = f"{self.cpa_name} <{self.smtp_user}>"
        msg["To"] = to_email
        msg["Subject"] = f"Re: {original_subject}"
        msg["Reply-To"] = self.smtp_user
        msg.attach(MIMEText(response_content, "plain"))

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_app_password)
                server.send_message(msg)
            return True, f"Response sent successfully to {to_email}"
        except Exception as e:
            log.exception("Failed sending response to %s", to_email)
            return False, f"Failed to send response: {e}"
