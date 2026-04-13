"""
Debug test for MCP server - isolated test without full server startup
"""
import sys
import asyncio
import time

sys.path.insert(0, 'C:/Users/steevenz/MCP/mcp-cct-server')

async def run_complexity_detection():
    """Test just the complexity detection - fastest test"""
    print("=" * 50)
    print("TEST 1: Complexity Detection Only")
    print("=" * 50)
    
    from src.tools.simplified_tools import _detect_complexity, TaskComplexity
    
    # Test case 1: Simple problem
    start = time.time()
    result1 = _detect_complexity("Create a function to add two numbers", 0)
    elapsed1 = time.time() - start
    print(f"✅ Simple test: {result1.value} (took {elapsed1:.3f}s)")
    
    # Test case 2: Complex problem
    start = time.time()
    complex_problem = "Design a secure microservices architecture with API gateway, authentication, and database sharding for 1M users. Must support horizontal scaling."
    result2 = _detect_complexity(complex_problem, 0)
    elapsed2 = time.time() - start
    print(f"✅ Complex test: {result2.value} (took {elapsed2:.3f}s)")
    
    print()

async def run_orchestrator_init():
    """Test orchestrator initialization"""
    print("=" * 50)
    print("TEST 2: Orchestrator Initialization")
    print("=" * 50)
    
    from src.engines.orchestrator import CognitiveOrchestrator
    from src.engines.memory.manager import MemoryManager
    from src.engines.sequential.engine import SequentialEngine
    from src.modes.registry import CognitiveEngineRegistry
    from src.analysis.scoring_engine import ScoringEngine
    from src.engines.fusion.orchestrator import FusionOrchestrator
    from src.engines.fusion.router import AutomaticPipelineRouter
    
    start = time.time()
    print("Initializing MemoryManager...")
    memory = MemoryManager()
    print(f"✅ MemoryManager ready (took {time.time() - start:.3f}s)")
    
    start = time.time()
    print("Initializing SequentialEngine...")
    sequential = SequentialEngine(memory)
    print(f"✅ SequentialEngine ready (took {time.time() - start:.3f}s)")
    
    start = time.time()
    print("Initializing ScoringEngine...")
    scoring = ScoringEngine()
    print(f"✅ ScoringEngine ready (took {time.time() - start:.3f}s)")
    
    start = time.time()
    print("Initializing FusionOrchestrator...")
    fusion = FusionOrchestrator(memory=memory, scoring=scoring, sequential=sequential)
    print(f"✅ FusionOrchestrator ready (took {time.time() - start:.3f}s)")
    
    start = time.time()
    print("Initializing AutomaticPipelineRouter...")
    router = AutomaticPipelineRouter(scoring_engine=scoring)
    print(f"✅ AutomaticPipelineRouter ready (took {time.time() - start:.3f}s)")
    
    start = time.time()
    print("Initializing CognitiveEngineRegistry...")
    registry = CognitiveEngineRegistry(
        memory_manager=memory,
        sequential_engine=sequential,
        fusion_orchestrator=fusion
    )
    print(f"✅ CognitiveEngineRegistry ready (took {time.time() - start:.3f}s)")
    
    start = time.time()
    print("Initializing Master CognitiveOrchestrator...")
    orchestrator = CognitiveOrchestrator(
        memory_manager=memory,
        sequential_engine=sequential,
        registry=registry,
        fusion_engine=fusion,
        router=router
    )
    print(f"✅ Master Orchestrator ready (took {time.time() - start:.3f}s)")
    
    return orchestrator

async def run_session_start():
    """Test actual session start"""
    print("=" * 50)
    print("TEST 3: Session Start (The Problem Area)")
    print("=" * 50)
    
    orchestrator = await run_orchestrator_init()
    
    print("\nStarting session with timeout...")
    
    # Test with timeout
    try:
        start = time.time()
        result = orchestrator.start_session(
            "Design a secure API authentication system",
            "balanced",
            None
        )
        elapsed = time.time() - start
        print(f"✅ Session started successfully in {elapsed:.3f}s")
        print(f"   Session ID: {result.get('session_id', 'N/A')}")
        return result
    except Exception as e:
        print(f"❌ Session start failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Run all tests"""
    print("\n" + "=" * 50)
    print("CCT MCP SERVER DEBUG TEST")
    print("=" * 50 + "\n")
    
    # Test 1: Fast test
    await run_complexity_detection()
    
    # Test 2 & 3: Full orchestrator test
    result = await run_session_start()
    
    print("\n" + "=" * 50)
    if result:
        print("✅ ALL TESTS PASSED - Server should work!")
    else:
        print("❌ TESTS FAILED - Check errors above")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
