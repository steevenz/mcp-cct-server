
import os
import sys
import uuid
import gc
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd())))

from src.engines.memory.manager import MemoryManager
from src.core.models.enums import CCTProfile, ThoughtType, ThinkingStrategy
from src.tools.simplified import TaskComplexity
from src.core.models.contexts import SequentialContext
from src.core.models.domain import EnhancedThought

def safe_remove(path: str) -> None:
    for _ in range(10):
        try:
            if os.path.exists(path):
                os.remove(path)
            return
        except PermissionError:
            time.sleep(0.05)

def test_session_persistence():
    print("Testing Session Persistence...")
    db_path = "test_memory.db"
    safe_remove(db_path)
        
    manager = MemoryManager(db_path=db_path)
    
    # 1. Create a session
    problem = "How to build a sustainable city on Mars?"
    session = manager.create_session(
        problem_statement=problem,
        profile=CCTProfile.BALANCED,
        estimated_thoughts=5,
        complexity=TaskComplexity.COMPLEX.value
    )
    
    session_id = session.session_id
    print(f"Created session: {session_id}")
    
    # 2. Verify it exists in DB
    retrieved = manager.get_session(session_id)
    assert retrieved is not None
    assert retrieved.problem_statement == problem
    assert retrieved.complexity == TaskComplexity.COMPLEX.value
    print("Session retrieval verified.")
    
    # 3. Add a thought
    thought = EnhancedThought(
        id=f"thought_{uuid.uuid4().hex[:8]}",
        content="We need to consider radiation shielding and oxygen production.",
        thought_type=ThoughtType.ANALYSIS,
        strategy=ThinkingStrategy.FIRST_PRINCIPLES,
        sequential_context=SequentialContext(
            thought_number=1,
            estimated_total_thoughts=5,
            next_thought_needed=True
        )
    )
    
    manager.save_thought(session_id, thought)
    print(f"Saved thought: {thought.id}")
    
    # 4. Verify thought persistence
    session_with_thought = manager.get_session(session_id)
    assert thought.id in session_with_thought.history_ids
    print("Thought history update verified.")
    
    # 6. Clean up
    del manager
    gc.collect()
    safe_remove(db_path)
    safe_remove(f"{db_path}-wal")
    safe_remove(f"{db_path}-shm")
        
    print("All persistence tests passed!")

if __name__ == "__main__":
    try:
        test_session_persistence()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
