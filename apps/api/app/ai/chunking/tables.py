class TableSplitter:
    @staticmethod
    def extract_table_chunks(normalized_content: dict) -> list[dict]:
        """Converts tabular structures into independent chunks with headers details."""
        tables = normalized_content.get("tables", [])
        chunks = []
        for idx, table in enumerate(tables):
            grid = table.get("data", [])
            sheet = table.get("sheet_name")
            
            # Format matrix rows to string representation
            rows_str = []
            for row in grid:
                rows_str.append(" | ".join([str(val) for val in row]))
            table_text = f"Sheet: {sheet}\n" if sheet else ""
            table_text += f"Table Index {idx + 1}\n"
            table_text += "\n".join(rows_str)
            
            chunks.append({
                "content": table_text.strip(),
                "metadata": {
                    "type": "table",
                    "table_index": idx + 1,
                    "sheet_name": sheet
                }
            })
        return chunks
