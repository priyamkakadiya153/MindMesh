import json
import logging
import re
from typing import List, Dict, Any, Optional
from app.ai.llm.factory import LLMProviderFactory
from app.agents.exceptions import AgentException

logger = logging.getLogger(__name__)

class TaskDecomposer:
    @staticmethod
    async def decompose(
        goal: str,
        tools_metadata: List[Dict[str, Any]],
        use_llm: bool = True
    ) -> List[Dict[str, Any]]:
        """Decomposes a goal into a list of planning task nodes."""
        if use_llm:
            try:
                # Retrieve Gemini provider
                provider = LLMProviderFactory.get_provider("gemini")
                if provider and getattr(provider, "api_key", None):
                    return await TaskDecomposer._decompose_with_llm(goal, tools_metadata, provider)
            except Exception as e:
                logger.warning(f"LLM decomposition failed, falling back to rules: {str(e)}")

        # Fallback to Rule-based Decomposer
        return TaskDecomposer._decompose_with_rules(goal, tools_metadata)

    @staticmethod
    async def _decompose_with_llm(
        goal: str,
        tools_metadata: List[Dict[str, Any]],
        provider: Any
    ) -> List[Dict[str, Any]]:
        # Format tools description for prompt
        tools_desc = []
        for t in tools_metadata:
            tools_desc.append({
                "name": t.get("name"),
                "description": t.get("description"),
                "input_schema": t.get("input_schema")
            })

        system_prompt = (
            "You are an expert AI Planning Assistant.\n"
            "Decompose the user's goal into a list of structured task steps.\n"
            "Each task step represents a tool call. You must only use tools from the available tools list.\n"
            "To reference outputs from a previous step (e.g. an ID returned by a project creation step), use the template string format: ${step_id.result.field_name} (e.g. ${step_1.result.id}).\n"
            "Output must be a JSON array of task objects with fields: id, tool, input, dependencies.\n"
            "Do not output markdown codeblocks, prefix or suffix. Output raw JSON only.\n"
            f"Available tools:\n{json.dumps(tools_desc, indent=2)}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Decompose goal: {goal}"}
        ]

        res = await provider.generate(messages=messages, temperature=0.0)
        content = res.get("content", "").strip()

        # Clean JSON if LLM returned markdown code blocks
        if content.startswith("```"):
            # Strip block formatting
            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"^```\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        
        try:
            tasks = json.loads(content)
            if isinstance(tasks, list):
                return tasks
            elif isinstance(tasks, dict) and "tasks" in tasks:
                return tasks["tasks"]
            raise ValueError("Parsed output was not a list of tasks.")
        except Exception as e:
            logger.error(f"Error parsing LLM response as JSON: {content}. Error: {str(e)}")
            raise AgentException("Failed to generate plan structure from LLM output.")

    @staticmethod
    def _decompose_with_rules(goal: str, tools_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rule-based pattern matching fallback for goal decomposition."""
        goal_lower = goal.lower()
        tasks = []

        # 1. Project creation matching
        # Example: "Create project 'Design Sprint' in workspace 'ws-123' and add task 'Wireframes'"
        proj_match = re.search(r"create\s+project\s+['\"]?([^'\"]+)['\"]?", goal_lower)
        proj_id_ref = "step_1"
        
        if proj_match:
            proj_name = proj_match.group(1).title()
            tasks.append({
                "id": "step_1",
                "tool": "create_project",
                "input": {
                    "name": proj_name
                },
                "dependencies": []
            })
        else:
            proj_id_ref = None

        # 2. Task creation matching
        # E.g. "and create task 'Prepare specs'" or "assign task 'Write tests'"
        task_matches = re.findall(r"(?:create|add|assign)\s+task\s+['\"]?([^'\"]+)['\"]?", goal_lower)
        
        for idx, task_desc in enumerate(task_matches):
            step_id = f"step_task_{idx+1}"
            deps = []
            task_input = {
                "description": task_desc.capitalize()
            }
            if proj_id_ref:
                task_input["project_id"] = f"${{{proj_id_ref}.result.id}}"
                deps.append(proj_id_ref)
                
            tasks.append({
                "id": step_id,
                "tool": "create_task",
                "input": task_input,
                "dependencies": deps
            })

        # 3. Notification dispatch matching
        # E.g. "notify user 'usr-123' with message 'done'"
        notify_match = re.search(r"notify\s+user\s+['\"]?([^'\"]+)['\"]?\s+with\s+message\s+['\"]?([^'\"]+)['\"]?", goal_lower)
        if notify_match:
            recipient_id = notify_match.group(1)
            msg = notify_match.group(2).capitalize()
            
            deps = []
            if tasks:
                # Notify after tasks/project creation is done
                deps = [t["id"] for t in tasks]
                
            tasks.append({
                "id": f"step_notify",
                "tool": "send_notification",
                "input": {
                    "recipient_id": recipient_id,
                    "message": msg
                },
                "dependencies": deps
            })

        # Default fallback if nothing matches
        if not tasks:
            # Create a simple search documents task as default
            tasks.append({
                "id": "step_search",
                "tool": "search_documents",
                "input": {"query": goal, "limit": 5},
                "dependencies": []
            })

        return tasks
