from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Workspace:
    id: str
    name: str
    created_at: datetime
    users: List[str] = None
    api_keys: List[str] = None

    def __post_init__(self):
        if self.users is None:
            self.users = []
        if self.api_keys is None:
            self.api_keys = []
