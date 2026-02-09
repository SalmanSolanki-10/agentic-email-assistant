from __future__ import annotations

import re
from typing import Dict, List


class EmailClassifier:
    """Heuristic classifier for determining complexity and extracting key info."""

    def __init__(self) -> None:
        self.basic_keywords: List[str] = [
            "home office", "deduction", "write off", "business expense",
            "quarterly tax", "estimated tax", "simple question", "quick question",
            "mileage", "receipt", "documentation", "forms", "deadline",
            "business meal", "travel expense", "depreciation",
        ]

        self.intermediate_keywords: List[str] = [
            "tax planning", "strategy", "incorporation", "llc", "partnership",
            "retirement plan", "investment", "audit preparation", "bookkeeping",
            "payroll", "sales tax", "state tax", "s-corp", "sole proprietorship",
        ]

        self.complex_keywords: List[str] = [
            "merger", "acquisition", "forensic", "litigation", "investigation",
            "estate planning", "trust", "international tax", "transfer pricing",
            "irs investigation", "penalty abatement", "appeal", "representation",
            "audit notice", "irs audit", "urgent",
        ]

    def classify(self, content: str) -> str:
        c = content.lower()
        basic = sum(1 for k in self.basic_keywords if k in c)
        inter = sum(1 for k in self.intermediate_keywords if k in c)
        complex_ = sum(1 for k in self.complex_keywords if k in c)

        # Bias towards higher complexity if there is any strong complex signal
        if complex_ > 0 or ("audit" in c and "irs" in c):
            return "complex"
        if inter >= max(1, basic):
            return "intermediate"
        return "basic"

    def extract_key_info(self, content: str) -> Dict:
        # Very lightweight extraction for dates, amounts, and entities.
        info: Dict = {}

        date_matches = re.findall(r"\b(?:\d{1,2}[/-])?\d{1,2}[/-]\d{2,4}\b", content)
        if date_matches:
            info["dates"] = list(dict.fromkeys(date_matches))[:5]

        money_matches = re.findall(r"\$\s?\d[\d,]*(?:\.\d{2})?", content)
        if money_matches:
            info["amounts"] = list(dict.fromkeys(money_matches))[:5]

        if re.search(r"\bW-2\b", content, re.I):
            info.setdefault("documents", []).append("W-2")
        if re.search(r"\b1099\b", content, re.I):
            info.setdefault("documents", []).append("1099")

        return info
