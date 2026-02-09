from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class EmailInteraction:
    timestamp: str
    sender: str
    subject: str
    content: str
    complexity: str
    response: str
    processing_time: float
    reply_sent: bool = False
    reply_status: str = ""
    message_id: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)
