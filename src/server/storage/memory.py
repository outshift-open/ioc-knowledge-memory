from typing import Dict, Optional, List
import threading
from server.models.workspace import Workspace
from server.models.user import User
from server.models.api_key import ApiKey


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
                users_to_delete = [user_id for user_id, user in self._users.items() 
                                 if user.workspace_id == workspace_id]
                for user_id in users_to_delete:
                    del self._users[user_id]
                
                api_keys_to_delete = [key_id for key_id, api_key in self._api_keys.items() 
                                    if api_key.workspace_id == workspace_id]
                for key_id in api_keys_to_delete:
                    del self._api_keys[key_id]
                
                del self._workspaces[workspace_id]
                return True
            return False
    
    def create_user(self, user: User) -> None:
        with self._lock:
            self._users[user.id] = user
            if user.workspace_id in self._workspaces:
                workspace = self._workspaces[user.workspace_id]
                if user.id not in workspace.users:
                    workspace.users.append(user.id)
    
    def get_user(self, user_id: str) -> Optional[User]:
        with self._lock:
            return self._users.get(user_id)
    
    def list_users(self) -> Dict[str, User]:
        with self._lock:
            return self._users.copy()
    
    def get_users_by_workspace(self, workspace_id: str) -> List[User]:
        with self._lock:
            return [user for user in self._users.values() if user.workspace_id == workspace_id]
    
    def delete_user(self, user_id: str) -> bool:
        with self._lock:
            if user_id in self._users:
                user = self._users[user_id]
                if user.workspace_id in self._workspaces:
                    workspace = self._workspaces[user.workspace_id]
                    if user_id in workspace.users:
                        workspace.users.remove(user_id)
                
                del self._users[user_id]
                return True
            return False
    
    def create_api_key(self, api_key: ApiKey) -> None:
        with self._lock:
            self._api_keys[api_key.id] = api_key
    
    def get_api_key(self, api_key_id: str) -> Optional[ApiKey]:
        with self._lock:
            return self._api_keys.get(api_key_id)
    
    def list_api_keys(self) -> Dict[str, ApiKey]:
        with self._lock:
            return self._api_keys.copy()
    
    def get_api_keys_by_workspace(self, workspace_id: str) -> List[ApiKey]:
        with self._lock:
            return [api_key for api_key in self._api_keys.values() if api_key.workspace_id == workspace_id]
    
    def delete_api_key(self, api_key_id: str) -> bool:
        with self._lock:
            if api_key_id in self._api_keys:
                del self._api_keys[api_key_id]
                return True
            return False


storage = InMemoryStorage()