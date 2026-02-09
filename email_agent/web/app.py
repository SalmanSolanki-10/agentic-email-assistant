from __future__ import annotations

import logging
from typing import Optional

from flask import Flask, jsonify, request, render_template

from ..config import Settings
from ..core.processor import EmailProcessor
from ..email.imap_monitor import RealEmailMonitor

log = logging.getLogger(__name__)


def create_app(settings: Settings, processor: EmailProcessor, monitor: Optional[RealEmailMonitor] = None) -> Flask:
    app = Flask(__name__, template_folder="../templates")

    @app.get("/")
    def index():
        return render_template("index.html", email=settings.gmail_address)

    @app.get("/api/stats")
    def stats():
        return jsonify(processor.get_stats())

    @app.get("/api/interactions")
    def interactions():
        return jsonify(processor.get_interactions())

    @app.post("/api/v1/agent/")
    def agent_respond():
        data = request.get_json(force=True, silent=True) or {}
        user_query = data.get("query", "")
        sender = data.get("sender", "external_source")
        subject = data.get("subject", "")
        response = processor.agent.generate(user_query, sender, subject)
        return jsonify({"response": response})

    if monitor is not None:
        @app.post("/api/monitor/start")
        def start_monitor():
            monitor.start(lambda s, sub, body, mid: processor.process_email_with_reply(s, sub, body, mid))
            return jsonify({"ok": True})

        @app.post("/api/monitor/stop")
        def stop_monitor():
            monitor.stop()
            return jsonify({"ok": True})

    return app
