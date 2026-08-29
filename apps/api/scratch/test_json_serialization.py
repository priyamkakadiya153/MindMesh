import json
import sys
import os
from uuid import uuid4

sys.path.insert(0, os.path.abspath("."))

from app.actions.types import ActionProposal, ActionIntentType, ActionStatus

def test_serialization():
    prop = ActionProposal(
        proposal_id=f"prop-{str(uuid4())[:8]}",
        intent_type=ActionIntentType.CREATE_TASK,
        title="Create Task: Review deployment report",
        description="Action proposal to create task 'Review deployment report'.",
        parameters={"title": "Review deployment report", "due_date_str": "tomorrow"},
        workspace_id=str(uuid4()),
        user_id=str(uuid4()),
        confirmation_required=True,
        status=ActionStatus.READY_FOR_CONFIRMATION
    )

    d = prop.dict()
    print("Raw prop.dict():", d)

    try:
        raw_json = json.dumps(d)
        print("json.dumps(d) WITHOUT default=str succeeded:", raw_json)
    except Exception as e:
        print("json.dumps(d) WITHOUT default=str FAILED WITH ERROR:", type(e), e)

    safe_json = json.dumps(d, default=str)
    print("json.dumps(d, default=str) SUCCEEDED:", safe_json)

    parsed_dict = json.loads(safe_json)
    print("Parsed JSON dict:", parsed_dict)
    assert parsed_dict["intent_type"] == "CREATE_TASK" or parsed_dict["intent_type"] == "create_task"
    assert parsed_dict["status"] == "READY_FOR_CONFIRMATION"
    print("ALL JSON SERIALIZATION CHECKS PASSED!")

if __name__ == "__main__":
    test_serialization()
