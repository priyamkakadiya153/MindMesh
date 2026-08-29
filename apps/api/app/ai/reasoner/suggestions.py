from typing import List, Dict, Any

class FollowUpGenerator:
    """Dynamically generates relevant follow-up query suggestions based on user

    intent and retrieved entities.

    """

    @classmethod
    def generate(cls, intent_info: Dict[str, Any], answer_text: str) -> List[str]:
        intent = intent_info.get("primary_intent", "FACT_LOOKUP")
        entities = intent_info.get("entities", [])
        entity_name = entities[0].title() if entities else "this project"

        suggestions: List[str] = []

        if intent == "DECISION_LOOKUP":
            suggestions.append(f"Why did we make the {entity_name} decision?")
            suggestions.append(f"What tasks resulted from the {entity_name} decision?")
            suggestions.append("Who agreed to this decision?")
        elif intent == "WHY_QUERY":
            suggestions.append(f"Which conversation produced the {entity_name} decision?")
            suggestions.append(f"What documents support this {entity_name} decision?")
            suggestions.append(f"What task resulted from the {entity_name} decision?")
        elif intent == "WHO_QUERY":
            suggestions.append(f"What decision did we make about {entity_name}?")
            suggestions.append("Show the original conversation text.")
        elif intent == "TASK_LOOKUP":
            suggestions.append(f"What decision led to these {entity_name} tasks?")
            suggestions.append("What is the current status of these tasks?")
        else:
            suggestions.append(f"What is connected to {entity_name}?")
            suggestions.append(f"Show the timeline history of {entity_name}.")
            suggestions.append(f"Why did we choose this approach for {entity_name}?")

        return suggestions[:3]
