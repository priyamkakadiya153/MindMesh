import re
from datetime import datetime, timedelta

def extract_entities(query: str) -> dict:
    """Extracts search filters (tags, workspace, project, author, file_type, dates) from query string."""
    filters = {}
    
    # 1. Key-Value filter pattern extraction (e.g., tag:kubernetes project:docs author:john)
    kv_pattern = r'\b(\w+):([\w\-]+)\b'
    matches = re.findall(kv_pattern, query)
    for k, v in matches:
        k_lower = k.lower()
        if k_lower in ("tag", "tags"):
            filters["tag"] = v
        elif k_lower == "project":
            filters["project"] = v
        elif k_lower == "workspace":
            filters["workspace"] = v
        elif k_lower == "author":
            filters["author"] = v
        elif k_lower in ("type", "filetype", "ext"):
            filters["file_type"] = v
            
    # 2. Natural language pattern extractions
    query_lower = query.lower()
    
    # Parse file type indicators
    if "pdf" in query_lower:
        filters["file_type"] = "pdf"
    elif "markdown" in query_lower or " md " in f" {query_lower} ":
        filters["file_type"] = "md"
        
    # Parse date ranges indicators
    now = datetime.utcnow()
    if "yesterday" in query_lower:
        filters["created_after"] = (now - timedelta(days=1)).isoformat()
    elif "last week" in query_lower:
        filters["created_after"] = (now - timedelta(days=7)).isoformat()
    elif "last month" in query_lower:
        filters["created_after"] = (now - timedelta(days=30)).isoformat()
        
    return filters
