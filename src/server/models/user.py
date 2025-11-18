from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: str
    name: str
    email: str
    workspace_id: str
    created_at: datetime