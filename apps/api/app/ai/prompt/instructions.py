from typing import Optional

class OutputInstructions:
    @staticmethod
    def get_format_instructions(format_type: str = "markdown") -> str:
        """Returns standard output format formatting rules for LLM adherence."""
        normalized = (format_type or "markdown").lower()
        
        if normalized == "json":
            return (
                "RESPONSE FORMAT REQUIREMENT:\n"
                "Your final response MUST be formatted strictly as a single JSON object. Do not wrap in markdown code blocks. "
                "The JSON must have the following keys:\n"
                '{\n'
                '  "answer": "A detailed, markdown-formatted grounded answer text with inline [X] citations.",\n'
                '  "citations": [\n'
                '     {"source_index": X, "reason": "Brief explanation of cited content"}\n'
                '  ]\n'
                '}'
            )
        elif normalized == "summary":
            return (
                "RESPONSE FORMAT REQUIREMENT:\n"
                "Provide a bulleted list of key findings, followed by a section outlining decisions, and a list of action items."
            )
        else:
            # Default markdown
            return (
                "RESPONSE FORMAT REQUIREMENT:\n"
                "Provide your response in clear, readable Markdown format. Use bold headers, bullet lists, or tables where appropriate."
            )
