from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    type: str
    data: Any = None