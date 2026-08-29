from typing import List, Dict, Any

class PromptFormatter:
    @staticmethod
    def format_messages_payload(
        system_prompt: str,
        history: List[Dict[str, str]],
        user_message: str
    ) -> List[Dict[str, str]]:
        """Compiles system prompt, history messages, and active user query into chat message list format."""
        payload = []
        
        # 1. System Prompt
        if system_prompt:
            payload.append({"role": "system", "content": system_prompt})
            
        # 2. History
        for msg in history:
            role = msg.get("role") or "user"
            content = msg.get("content") or ""
            payload.append({"role": role, "content": content})
            
        # 3. User Message
        payload.append({"role": "user", "content": user_message})
        
        return payload
