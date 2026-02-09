#!/usr/bin/env python3
from __future__ import annotations

import logging

from email_agent.config import Settings
from email_agent.logging_utils import setup_logging
from email_agent.core.processor import EmailProcessor
from email_agent.email.imap_monitor import RealEmailMonitor
from email_agent.web.app import create_app


def main() -> None:
    setup_logging()
    log = logging.getLogger("main")

    settings = Settings.from_env()
    processor = EmailProcessor(settings)

    monitor = RealEmailMonitor(
        imap_host=settings.imap_host,
        imap_port=settings.imap_port,
        gmail_address=settings.gmail_address,
        gmail_app_password=settings.gmail_app_password,
        poll_seconds=settings.poll_seconds,
    )

    # Start monitoring immediately (safe: no-op if not configured)
    monitor.start(lambda s, sub, body, mid: processor.process_email_with_reply(s, sub, body, mid))

    app = create_app(settings, processor, monitor)
    log.info("Web UI: http://%s:%s", settings.web_host, settings.web_port)
    app.run(host=settings.web_host, port=settings.web_port, debug=settings.web_debug)


if __name__ == "__main__":
    main()

