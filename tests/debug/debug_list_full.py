import sys
import os
sys.path.append(os.getcwd())
import logging
from src.core.models.enums import SessionStatus
from src.engines.memory.manager import MemoryManager

# Setup basic logging to see what's happening
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_list_thinking_full():
    memory = MemoryManager()
    sessions = memory.list_sessions()
    print(f"Found {len(sessions)} sessions")
    
    status_filter = "all"
    
    for sid in sessions:
        print(f"Checking session {sid}")
        session = memory.get_session(sid)
        if not session:
            continue
            
        status = getattr(session, 'status', 'unknown')
        print(f"Status: {status}, Type: {type(status)}")
        
        # This was the logic in simplified_tools.py
        try:
            status_val = status.value if hasattr(status, 'value') else str(status)
            print(f"Status Val: {status_val}")
            
            if status == SessionStatus.ACTIVE:
                print("Status matches SessionStatus.ACTIVE")
            
            res = {
                "id": sid,
                "status": status.value if hasattr(status, 'value') else str(status),
                "profile": getattr(session, 'profile', 'balanced').value if hasattr(getattr(session, 'profile', None), 'value') else str(getattr(session, 'profile', 'balanced')),
            }
            print(f"Session Result: {res}")
        except Exception as e:
            print(f"!!! Error in session {sid}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_list_thinking_full()
