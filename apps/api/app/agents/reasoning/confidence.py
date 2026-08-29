class ConfidenceEngine:
    @staticmethod
    def calculate_score(details: dict) -> float:
        """Calculates a confidence score between 0.0 and 1.0 based on criteria."""
        success_rate = details.get("success_rate", 1.0)
        param_completion = details.get("param_completion", 1.0)
        policy_checks = details.get("policy_checks", 1.0)
        
        # Weighted avg
        score = (success_rate * 0.4) + (param_completion * 0.4) + (policy_checks * 0.2)
        return min(max(score, 0.0), 1.0)

    @staticmethod
    def resolve_level(score: float) -> str:
        """Maps numerical confidence score to High, Medium, or Low level."""
        if score >= 0.8:
            return "HIGH"
        elif score >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"
