import sys
import os

sys.path.insert(0, os.path.abspath("."))

from app.ai.understanding import SemanticUnderstandingEngine
from app.actions.classifier import ActionClassifier

queries = [
    ("A", "create a task"),
    ("C", "Create a task to review the report."),
    ("D", "Can you put reviewing the report on my todo list?"),
    ("E", "Remind me to review the files tomorrow."),
    ("F", "about remind me for review files"),
    ("G", "Remind me to review the files."),
    ("H", "What tasks do I have?"),
    ("I", "What reminders do I have?"),
    ("J", "what is 2 + 2?"),
    ("K", "What is an API?"),
    ("L", "Why is the deployment task blocked?")
]

print("\n================ SYSTEM ROUTING INTENT TEST MATRIX ================")
for code, q in queries:
    u = SemanticUnderstandingEngine.parse_request(q)
    p = ActionClassifier.classify(q)
    print(f"[{code}] Query: '{q}'")
    print(f"    Intent: {u.intent.value} | Capability: {u.required_capability.value}")
    if u.missing_information:
        print(f"    Missing Params: {u.missing_information}")
    if p:
        print(f"    Action Proposal: Title='{p.title}', Status='{p.status.value}'")
    print("-" * 65)

print("\nTesting Follow-Up State B ('review the report' with pending_action={'intent': 'CREATE_TASK', 'missing': ['title']})...")
u_b = SemanticUnderstandingEngine.parse_request("review the report", pending_action={"intent": "CREATE_TASK", "missing": ["title"]})
print(f"[B] Query: 'review the report' (Pending Task Fill)")
print(f"    Intent: {u_b.intent.value} | Capability: {u_b.required_capability.value}")
print(f"    Entities: {u_b.entities}")
print("===================================================================\n")
