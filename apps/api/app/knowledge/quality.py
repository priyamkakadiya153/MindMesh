class QualityAssessor:
    @staticmethod
    def assess_quality(normalized_content: dict) -> float:
        """Computes document extraction quality score between 0.0 and 1.0."""
        score = 1.0
        
        # 1. Deduct if there's no title
        if not normalized_content.get("title"):
            score -= 0.1
            
        # 2. Deduct if metadata keys are missing
        meta = normalized_content.get("metadata", {})
        if not meta or len(meta) == 0:
            score -= 0.1
            
        # 3. Deduct if structural paragraphs are empty
        paragraphs = normalized_content.get("paragraphs", [])
        if not paragraphs:
            score -= 0.3
            
        # 4. Deduct if headings are totally empty (low structural hierarchy score)
        sections = normalized_content.get("sections", [])
        if not sections:
            score -= 0.1
            
        # 5. Deduct if statistics is missing
        if not normalized_content.get("statistics"):
            score -= 0.1
            
        return float(max(0.0, min(1.0, score)))
