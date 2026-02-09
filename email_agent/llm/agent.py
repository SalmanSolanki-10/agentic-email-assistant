from __future__ import annotations

import logging
import os
from typing import Optional

log = logging.getLogger(__name__)


class AgenticResponder:
    """Generates email replies using an LLM, optionally with web tools."""

    def __init__(
        self,
        ollama_model: str = "llama3",
        enable_tools: bool = True,
        tavily_api_key: str = "",
        langchain_api_key: str = "",
        langsmith_tracing: bool = False,
        langsmith_endpoint: str = "https://api.smith.langchain.com",
        langchain_project: str = "General Purpose Email Agent",
        max_iterations: int = 3,
    ) -> None:
        self.ollama_model = ollama_model
        self.enable_tools = enable_tools
        self.tavily_api_key = tavily_api_key
        self.langchain_api_key = langchain_api_key
        self.langsmith_tracing = langsmith_tracing
        self.langsmith_endpoint = langsmith_endpoint
        self.langchain_project = langchain_project
        self.max_iterations = max_iterations

        self._agent = None
        self._fallback_chain = None

    def _ensure_env(self) -> None:
        # Only set if provided; never hardcode secrets.
        if self.langsmith_tracing:
            os.environ["LANGSMITH_TRACING"] = "true"
        if self.langsmith_endpoint:
            os.environ["LANGSMITH_ENDPOINT"] = self.langsmith_endpoint
        if self.langchain_api_key:
            os.environ["LANGCHAIN_API_KEY"] = self.langchain_api_key
        if self.langchain_project:
            os.environ["LANGCHAIN_PROJECT"] = self.langchain_project
        if self.tavily_api_key:
            os.environ["TAVILY_API_KEY"] = self.tavily_api_key

    def _build_agent(self):
        self._ensure_env()

        from langchain.agents import initialize_agent, AgentType
        from langchain_community.llms import Ollama

        tools = []
        if self.enable_tools and self.tavily_api_key:
            from langchain_community.tools.tavily_search import TavilySearchResults
            tools = [TavilySearchResults(max_results=3)]

        prefix = """You are a helpful email assistant.
Follow the ReAct format strictly.

When you have enough information, write the final answer on a new line EXACTLY as:
Final Answer: <your concise 2-4 sentence reply for the sender>

Rules:
- Keep the final answer short, factual, and directly responsive to the email.
- Do NOT include tool logs, Observations, or Thoughts in the final answer.
"""

        suffix = """Use tools if needed, but keep it brief.

Question:
{input}

{agent_scratchpad}

Remember: end with one line beginning with `Final Answer:` only."""

        return initialize_agent(
            tools=tools,
            llm=Ollama(model=self.ollama_model),
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            agent_kwargs={"prefix": prefix, "suffix": suffix},
            verbose=False,
            max_iterations=self.max_iterations,
            early_stopping_method="generate",
            handle_parsing_errors=True,
        )

    def _build_fallback_chain(self):
        self._ensure_env()
        from langchain_community.llms import Ollama
        from langchain_core.prompts import PromptTemplate
        from langchain.chains import LLMChain

        prompt = PromptTemplate.from_template(
            """You are an email assistant. Reply to the sender in 2–4 concise sentences.
- Be helpful and specific.
- No tool logs or analysis.
- If you lack exact info, ask 1 clarifying question.

From: {sender}
Subject: {subject}
Email:
{email_body}
"""
        )
        return LLMChain(llm=Ollama(model=self.ollama_model), prompt=prompt)

    def generate(self, email_body: str, sender: str, subject: str) -> str:
        # 1) Agent (tools optional)
        try:
            if self._agent is None:
                self._agent = self._build_agent()

            task = f"""Given the email below, respond in 2-4 concise sentences.

Rules:
- If uncertain or the question requires current facts, use tools (if available), then answer.
- Do NOT include thoughts, tool logs, or steps.
- If you use the web, add a short 'Sources:' line with 1-2 URLs.

From: {sender}
Subject: {subject}

Email Body:
{email_body}
"""
            result = self._agent.invoke({"input": task})
            response = (result.get("output") or "").strip()
            if "Final Answer:" in response:
                response = response.split("Final Answer:", 1)[-1].strip()
            if response:
                return response
        except Exception as e:
            log.exception("Agent generation failed: %s", e)

        # 2) Fallback: direct LLM
        try:
            if self._fallback_chain is None:
                self._fallback_chain = self._build_fallback_chain()
            res = self._fallback_chain.invoke({"sender": sender, "subject": subject, "email_body": email_body})
            # langchain versions differ: sometimes "text", sometimes "output_text"
            return (res.get("text") or res.get("output_text") or "").strip() or "Could you share a bit more detail so I can answer accurately?"
        except Exception as e:
            log.exception("Fallback LLM failed: %s", e)
            return "Could you share a bit more detail so I can answer accurately?"
