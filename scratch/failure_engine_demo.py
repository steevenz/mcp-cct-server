import asyncio
import uuid
from src.engines.orchestrator import CognitiveOrchestrator
from src.core.models.enums import ThinkingStrategy, ThoughtType
from src.core.models.domain import EnhancedThought
from src.engines.memory.manager import MemoryManager

async def test_failure_logging():
    memory = MemoryManager()
    orchestrator = CognitiveOrchestrator(memory, None, None)
    
    # 1. Start a session
    sess = orchestrator.start_session("Test problem", "balanced")
    sid = sess["session_id"]
    
    # 2. Manually inject a thought into memory
    random_id = f"test_thought_{uuid.uuid4().hex[:8]}"
    thought = EnhancedThought(
        id=random_id,
        session_id=sid,
        content="This is a failed thought context",
        strategy=ThinkingStrategy.LINEAR,
        thought_type=ThoughtType.ANALYSIS,
        thought_number=1,
        sequential_context={"thought_id": random_id} # Minimal dummy
    )
    memory.save_thought(sid, thought)
    tid = thought.id
    print(f"Manually injected thought: {tid}")
    
    # 3. Log a failure via orchestrator
    failure_result = orchestrator.log_failure(
        session_id=sid,
        thought_id=tid,
        category="LOGIC_FLAW",
        reason="Circular reasoning detected.",
        correction="Verify root assumptions."
    )
    print(f"Failure logged result: {failure_result}")
    
    # 4. Verify in memory
    failures = memory.get_global_anti_patterns()
    found = any(f.thought_id == tid for f in failures)
    if found:
        print("Success: Anti-pattern persisted correctly!")
    else:
        print("Failure: Anti-pattern not found in memory.")

if __name__ == "__main__":
    asyncio.run(test_failure_logging())
