from typing import Dict, Any

class AgentConfig:
    def __init__(self, defaults: Dict[str, Any] = None):
        self._config = defaults or {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        self._config[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return self._config.copy()
