from typing import Dict, Optional
import threading
from models.workspace import Workspace
from models.user import User
from models.api_key import ApiKey


class InMemoryStorage:
    """Thread-safe in-memory storage for workspaces, users, and API keys"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._workspaces: Dict[str, Workspace] = {}
        self._users: Dict[str, User] = {}
        self._api_keys: Dict[str, ApiKey] = {}
    
    def create_workspace(self, workspace: Workspace) -> None:
        with self._lock:
            self._workspaces[workspace.id] = workspace
    
    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        with self._lock:
            return self._workspaces.get(workspace_id)
    
    def list_workspaces(self) -> Dict[str, Workspace]:
        with self._lock:
            return self._workspaces.copy()
    
    def workspace_exists(self, workspace_id: str) -> bool:
        with self._lock:
            return workspace_id in self._workspaces
    
    def update_workspace(self, workspace_id: str, workspace: Workspace) -> bool:
        with self._lock:
            if workspace_id in self._workspaces:
                self._workspaces[workspace_id] = workspace
                return True
            return False
    
    def delete_workspace(self, workspace_id: str) -> bool:
        with self._lock:
            if workspace_id in self._workspaces:
                del self._workspaces[workspace_id]
                return True
            return False
    
    def create_user(self, user: User) -> None:
        with self._lock:
            self._users[user.id] = user
    
    def get_user(self, user_id: str) -> Optional[User]:
        with self._lock:
            return self._users.get(user_id)
    
    def list_users(self) -> Dict[str, User]:
        with self._lock:
            return self._users.copy()
    
    def create_api_key(self, api_key: ApiKey) -> None:
        with self._lock:
            self._api_keys[api_key.id] = api_key
    
    def get_api_key(self, api_key_id: str) -> Optional[ApiKey]:
        with self._lock:
            return self._api_keys.get(api_key_id)
    
    def list_api_keys(self) -> Dict[str, ApiKey]:
        with self._lock:
            return self._api_keys.copy()


storage = InMemoryStorage()