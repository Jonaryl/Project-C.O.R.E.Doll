from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    id: str
    type: str
    timestamp: str
    source: str
    correlation_id: str
    data: Any = None