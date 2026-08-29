import logging

class AgentLogger:
    def __init__(self, agent_name: str, request_id: str):
        self.logger = logging.getLogger(f"agent.{agent_name}")
        self.request_id = request_id

    def info(self, msg: str, *args, **kwargs):
        self.logger.info(f"[{self.request_id}] {msg}", *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self.logger.error(f"[{self.request_id}] {msg}", *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(f"[{self.request_id}] {msg}", *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(f"[{self.request_id}] {msg}", *args, **kwargs)
