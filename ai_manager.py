import uuid
from typing import Dict, Any, Optional, List
import json
import os
from threading import Lock

class AIManager:
    def __init__(self):
        self.ai_registry: Dict[str, Dict[str, Any]] = {}
        self.data_dir = "ai_data"
        self.lock = Lock()
        self._load_ai_data()

    def _load_ai_data(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                with open(os.path.join(self.data_dir, filename), 'r') as f:
                    ai_data = json.load(f)
                    self.ai_registry[ai_data['id']] = ai_data

    def _save_ai_data(self, ai_id: str):
        filename = f"{ai_id}.json"
        with open(os.path.join(self.data_dir, filename), 'w') as f:
            json.dump(self.ai_registry[ai_id], f)

    def add_ai(self, ai_data: Dict[str, Any]) -> str:
        with self.lock:
            unique_id = str(uuid.uuid4())
            ai_data['id'] = unique_id
            self.ai_registry[unique_id] = ai_data
            self._save_ai_data(unique_id)
        return unique_id

    def get_ai(self, ai_id: str) -> Optional[Dict[str, Any]]:
        return self.ai_registry.get(ai_id)

    def get_all_ai(self) -> Dict[str, Dict[str, Any]]:
        return self.ai_registry

    def update_ai(self, ai_id: str, new_data: Dict[str, Any]) -> bool:
        with self.lock:
            if ai_id in self.ai_registry:
                self.ai_registry[ai_id].update(new_data)
                self._save_ai_data(ai_id)
                return True
        return False

    def delete_ai(self, ai_id: str) -> bool:
        with self.lock:
            if ai_id in self.ai_registry:
                del self.ai_registry[ai_id]
                os.remove(os.path.join(self.data_dir, f"{ai_id}.json"))
                return True
        return False

    def get_ai_by_type(self, ai_type: str) -> List[Dict[str, Any]]:
        return [ai for ai in self.ai_registry.values() if ai['type'] == ai_type]

    def get_ai_count(self) -> int:
        return len(self.ai_registry)

    def clear_all_ai(self):
        with self.lock:
            self.ai_registry.clear()
            for filename in os.listdir(self.data_dir):
                os.remove(os.path.join(self.data_dir, filename))