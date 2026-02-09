from __future__ import annotations

import email
import imaplib
import logging
import time
from datetime import datetime
from email.header import decode_header
from threading import Thread
from typing import Callable, Optional

log = logging.getLogger(__name__)


class RealEmailMonitor:
    """Monitors a Gmail account via IMAP for unread messages."""

    def __init__(self, imap_host: str, imap_port: int, gmail_address: str, gmail_app_password: str, poll_seconds: int = 30):
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.gmail_address = gmail_address
        self.gmail_app_password = gmail_app_password
        self.poll_seconds = poll_seconds

        self._monitoring = False
        self._thread: Optional[Thread] = None
        self._on_email: Optional[Callable[[str, str, str, str], None]] = None  # (sender_email, subject, body, message_id)

    def start(self, on_email: Callable[[str, str, str, str], None]) -> None:
        self._on_email = on_email
        self._monitoring = True
        self._thread = Thread(target=self._loop, daemon=True)
        self._thread.start()
        log.info("Started email monitoring for %s", self.gmail_address)

    def stop(self) -> None:
        self._monitoring = False
        log.info("Stopped email monitoring")

    def _loop(self) -> None:
        while self._monitoring:
            try:
                self.check_for_new_emails()
            except Exception:
                log.exception("Error during email polling loop")
            time.sleep(self.poll_seconds)

    def check_for_new_emails(self) -> None:
        if not self.gmail_address or not self.gmail_app_password:
            log.warning("IMAP not configured; set GMAIL_ADDRESS and GMAIL_APP_PASSWORD to enable monitoring.")
            return

        with imaplib.IMAP4_SSL(self.imap_host, self.imap_port) as mail:
            mail.login(self.gmail_address, self.gmail_app_password)
            mail.select("INBOX")

            # Only unread
            _result, message_ids = mail.search(None, "UNSEEN")
            if not message_ids or not message_ids[0]:
                return

            ids = message_ids[0].split()
            for msg_id in ids:
                try:
                    self._process_message(mail, msg_id)
                except Exception:
                    log.exception("Failed processing IMAP message %s", msg_id)

    def _process_message(self, mail: imaplib.IMAP4_SSL, msg_id: bytes) -> None:
        _result, msg_data = mail.fetch(msg_id, "(RFC822)")
        if not msg_data or not msg_data[0]:
            return

        raw = msg_data[0][1]
        m = email.message_from_bytes(raw)

        subject = self._decode_header(m.get("Subject")) or "No Subject"
        sender = self._decode_header(m.get("From", ""))
        message_id = (m.get("Message-ID") or "").strip()

        sender_email = self._extract_email_address(sender)
        if not sender_email:
            return

        # Avoid loops and system mail
        if sender_email.lower() == self.gmail_address.lower():
            return
        if "google.com" in sender_email.lower() or "no-reply" in sender_email.lower():
            return

        body = self._extract_body(m)

        if self._on_email:
            self._on_email(sender_email, subject, body, message_id or f"imap-{msg_id.decode(errors='ignore')}-{datetime.now().isoformat()}")

    @staticmethod
    def _decode_header(value: Optional[str]) -> str:
        if not value:
            return ""
        decoded = decode_header(value)[0]
        if isinstance(decoded[0], bytes):
            return decoded[0].decode(decoded[1] or "utf-8", errors="ignore")
        return str(decoded[0])

    @staticmethod
    def _extract_email_address(from_field: str) -> str:
        if "<" in from_field and ">" in from_field:
            return from_field.split("<", 1)[1].split(">", 1)[0].strip()
        return from_field.strip()

    @staticmethod
    def _extract_body(m: email.message.Message) -> str:
        if m.is_multipart():
            for part in m.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode("utf-8", errors="ignore")
            return ""
        payload = m.get_payload(decode=True)
        return payload.decode("utf-8", errors="ignore") if payload else ""
