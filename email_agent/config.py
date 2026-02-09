from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return v if v not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    # Gmail (IMAP read)
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    gmail_address: str = ""
    gmail_app_password: str = ""

    # Gmail (SMTP send)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_app_password: str = ""

    # Behavior
    cpa_name: str = "John Martinez"
    poll_seconds: int = 30
    state_path: str = "state/processed_message_ids.jsonl"

    # LLM / tools
    ollama_model: str = "llama3"
    enable_tools: bool = True
    tavily_api_key: str = ""
    langchain_api_key: str = ""  # LangSmith
    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langchain_project: str = "General Purpose Email Agent"

    # Web server
    web_host: str = "0.0.0.0"
    web_port: int = 5001
    web_debug: bool = False

    @staticmethod
    def from_env() -> "Settings":
        return Settings(
            gmail_address=_env("GMAIL_ADDRESS", "") or "",
            gmail_app_password=_env("GMAIL_APP_PASSWORD", "") or "",
            smtp_user=_env("SMTP_USER") or _env("GMAIL_ADDRESS", "") or "",
            smtp_app_password=_env("SMTP_APP_PASSWORD") or _env("GMAIL_APP_PASSWORD", "") or "",
            cpa_name=_env("CPA_NAME", "John Martinez") or "John Martinez",
            poll_seconds=int(_env("POLL_SECONDS", "30") or "30"),
            state_path=_env("STATE_PATH", "state/processed_message_ids.jsonl") or "state/processed_message_ids.jsonl",
            ollama_model=_env("OLLAMA_MODEL", "llama3") or "llama3",
            enable_tools=(_env("ENABLE_TOOLS", "true") or "true").lower() in ("1", "true", "yes", "y", "on"),
            tavily_api_key=_env("TAVILY_API_KEY", "") or "",
            langchain_api_key=_env("LANGCHAIN_API_KEY", "") or "",
            langsmith_tracing=(_env("LANGSMITH_TRACING", "false") or "false").lower() in ("1", "true", "yes", "y", "on"),
            langsmith_endpoint=_env("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com") or "https://api.smith.langchain.com",
            langchain_project=_env("LANGCHAIN_PROJECT", "General Purpose Email Agent") or "General Purpose Email Agent",
            web_host=_env("WEB_HOST", "0.0.0.0") or "0.0.0.0",
            web_port=int(_env("WEB_PORT", "5001") or "5001"),
            web_debug=(_env("WEB_DEBUG", "false") or "false").lower() in ("1", "true", "yes", "y", "on"),
        )

