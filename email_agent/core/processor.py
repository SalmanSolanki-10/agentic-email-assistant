from __future__ import annotations

import logging
import time
from datetime import datetime
from threading import Lock
from typing import Dict, List

from ..config import Settings
from ..core.models import EmailInteraction
from ..core.state import ProcessedMessageStore
from ..email.classifier import EmailClassifier
from ..email.responder import EmailResponder
from ..llm.agent import AgenticResponder

log = logging.getLogger(__name__)


class EmailProcessor:
    """Processes incoming emails, generates a reply, and sends it."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.classifier = EmailClassifier()
        self.responder = EmailResponder(settings.smtp_user, settings.smtp_app_password, settings.cpa_name)
        self.agent = AgenticResponder(
            ollama_model=settings.ollama_model,
            enable_tools=settings.enable_tools,
            tavily_api_key=settings.tavily_api_key,
            langchain_api_key=settings.langchain_api_key,
            langsmith_tracing=settings.langsmith_tracing,
            langsmith_endpoint=settings.langsmith_endpoint,
            langchain_project=settings.langchain_project,
        )

        self.state = ProcessedMessageStore(settings.state_path)

        self._lock = Lock()
        self._interactions: List[EmailInteraction] = []
        self._stats: Dict[str, float] = {
            "total_processed": 0,
            "basic_count": 0,
            "intermediate_count": 0,
            "complex_count": 0,
            "avg_processing_time": 0.0,
            "replies_sent": 0,
            "reply_success_rate": 0.0,
        }

    def process_email_with_reply(self, sender: str, subject: str, content: str, message_id: str) -> EmailInteraction:
        if message_id and self.state.contains(message_id):
            log.info("Skipping already processed message_id=%s", message_id)
            # Return a lightweight interaction record
            return EmailInteraction(
                timestamp=datetime.now().isoformat(),
                sender=sender,
                subject=subject,
                content=content,
                complexity="basic",
                response="(skipped duplicate)",
                processing_time=0.0,
                reply_sent=False,
                reply_status="Skipped duplicate",
                message_id=message_id,
            )

        start = time.time()
        complexity = self.classifier.classify(content)
        _key_info = self.classifier.extract_key_info(content)

        response = self.agent.generate(content, sender, subject)
        processing_time = time.time() - start

        reply_sent, reply_status = self.responder.send_response(
            smtp_host=self.settings.smtp_host,
            smtp_port=self.settings.smtp_port,
            to_email=sender,
            original_subject=subject,
            response_content=response,
        )

        interaction = EmailInteraction(
            timestamp=datetime.now().isoformat(),
            sender=sender,
            subject=subject,
            content=content,
            complexity=complexity,
            response=response,
            processing_time=processing_time,
            reply_sent=reply_sent,
            reply_status=reply_status,
            message_id=message_id,
        )

        # Persist message id immediately so restarts don't resend
        if message_id:
            self.state.add(message_id, interaction.timestamp)

        with self._lock:
            self._interactions.append(interaction)
            self._update_stats_locked(complexity, processing_time, reply_sent)

        return interaction

    def _update_stats_locked(self, complexity: str, processing_time: float, reply_sent: bool) -> None:
        self._stats["total_processed"] += 1
        key = f"{complexity}_count"
        if key in self._stats:
            self._stats[key] += 1

        if reply_sent:
            self._stats["replies_sent"] += 1

        total = self._stats["total_processed"]
        self._stats["reply_success_rate"] = (self._stats["replies_sent"] / total) * 100.0 if total else 0.0

        prev_avg = self._stats["avg_processing_time"]
        self._stats["avg_processing_time"] = ((prev_avg * (total - 1)) + processing_time) / total if total else 0.0

    def get_interactions(self) -> List[Dict]:
        with self._lock:
            return [i.to_dict() for i in self._interactions]

    def get_stats(self) -> Dict:
        with self._lock:
            return dict(self._stats)
