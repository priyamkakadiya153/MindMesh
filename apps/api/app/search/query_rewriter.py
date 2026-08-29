import re

ACRONYMS = {
    "k8s": "kubernetes",
    "auth": "authentication",
    "pg": "postgresql",
    "postgres": "postgresql",
    "ci": "continuous integration",
    "cd": "continuous deployment",
    "aws": "amazon web services",
    "gcp": "google cloud platform"
}

def rewrite_query(query: str) -> str:
    """Expands acronyms and normalizes term variations to improve search recall."""
    words = query.lower().split()
    rewritten = []
    
    for word in words:
        # Strip punctuation for matching
        clean = re.sub(r'[^\w]', '', word)
        if clean in ACRONYMS:
            rewritten.append(ACRONYMS[clean])
        else:
            rewritten.append(word)
            
    return " ".join(rewritten)
