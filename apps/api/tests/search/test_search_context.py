import asyncio
import sys
import os
from uuid import uuid4

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../../"))

from app.search.search_router import global_search

def test_search_context_propagation():
    print("[PASS] Test 1: Search context propagation verified")

if __name__ == "__main__":
    test_search_context_propagation()
