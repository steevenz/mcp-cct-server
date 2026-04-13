import sys
import os
sys.path.append(os.getcwd())
from src.core.models.enums import SessionStatus

class MockSession:
    def __init__(self):
        self.status = "active"
        self.profile = "balanced"
        self.problem_statement = "test"
        self.history_ids = []

session = MockSession()

def test_list_thinking_logic():
    status = getattr(session, 'status', 'unknown')
    
    # This was the logic in simplified_tools.py
    status_val = status.value if hasattr(status, 'value') else str(status)
    print(f"Status Val: {status_val}")
    
    if status == SessionStatus.ACTIVE:
        print("Status is ACTIVE")

    res = {
        "status": status.value if hasattr(status, 'value') else str(status),
        "profile": getattr(session, 'profile', 'balanced').value if hasattr(getattr(session, 'profile', None), 'value') else str(getattr(session, 'profile', 'balanced')),
    }
    print(f"Result: {res}")

if __name__ == "__main__":
    try:
        test_list_thinking_logic()
    except Exception as e:
        print(f"Caught error: {e}")
        import traceback
        traceback.print_exc()
