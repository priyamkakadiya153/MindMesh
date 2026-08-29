from typing import List, Dict, Any
from collections import Counter

class ConsensusFramework:
    @staticmethod
    def verify_consensus(outputs: List[Dict[str, Any]], match_key: str = "status") -> Dict[str, Any]:
        """Calculates majority consensus among multiple agent output payloads."""
        if not outputs:
            return {"consensus": False, "majority_value": None, "votes": 0}

        values = []
        for out in outputs:
            target = out.get("result", out) if isinstance(out, dict) else out
            val = target.get(match_key) if isinstance(target, dict) else None
            if val is not None:
                values.append(str(val))

        if not values:
            return {"consensus": False, "majority_value": None, "votes": 0}

        counter = Counter(values)
        majority_value, votes = counter.most_common(1)[0]
        
        # Require majority (> 50% of voting agents)
        total_votes = len(values)
        if votes > (total_votes / 2.0):
            matching_output = next(
                out for out in outputs
                if str((out.get("result", out) if isinstance(out, dict) else out).get(match_key)) == majority_value
            )
            return {
                "consensus": True,
                "majority_value": majority_value,
                "votes": votes,
                "total": total_votes,
                "output": matching_output
            }
        
        return {
            "consensus": False,
            "majority_value": None,
            "votes": votes,
            "total": total_votes
        }
