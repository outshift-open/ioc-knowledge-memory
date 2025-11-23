from dataclasses import dataclass
from datetime import datetime


@dataclass
class ApiKey:
    id: str
    key: str
    workspace_id: str
    created_at: datetime
