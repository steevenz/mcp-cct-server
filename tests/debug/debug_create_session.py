import sys
import os
sys.path.append(os.getcwd())
import logging
from src.core.models.enums import CCTProfile
from src.engines.memory.manager import MemoryManager

# Setup basic logging
logging.basicConfig(level=logging.DEBUG)

def test_create_session():
    memory = MemoryManager()
    
    # Test 1: Positional (legacy style)
    print("Testing Test 1: Positional (3 args)...")
    s1 = memory.create_session("test 1", CCTProfile.BALANCED, 3)
    print(f"Created s1: {s1.session_id}, thoughts: {s1.estimated_total_thoughts}, model: {s1.model_id}")
    
    # Test 2: Keyword (simplified tools style)
    print("\nTesting Test 2: Keyword (with model_id)...")
    s2 = memory.create_session(
        problem_statement="test 2",
        profile=CCTProfile.BALANCED,
        estimated_thoughts=5,
        model_id="test-model"
    )
    print(f"Created s2: {s2.session_id}, thoughts: {s2.estimated_total_thoughts}, model: {s2.model_id}")

if __name__ == "__main__":
    try:
        test_create_session()
        print("\nSUCCESS: All tests passed.")
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
