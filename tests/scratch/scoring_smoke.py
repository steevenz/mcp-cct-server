import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path("src").resolve()))

try:
    from analysis.scoring_engine import ScoringEngine
    from core.models.domain import EnhancedThought
    from core.models.contexts import SequentialContext
    from core.models.enums import ThoughtType, ThinkingStrategy
    
    # Initialize engine
    engine = ScoringEngine()
    
    # Create a dummy thought
    thought = EnhancedThought(
        id="test_1",
        content="This is a short test thought to verify cost precision.",
        thought_type=ThoughtType.PLANNING,
        strategy=ThinkingStrategy.LINEAR,
        sequential_context=SequentialContext(thought_number=1, total_thoughts=5)
    )
    
    # Run analysis
    metrics = engine.analyze_thought(thought, [], model_id="claude-3-5-sonnet-20240620")
    
    print(f"Metrics Output: {metrics.model_dump()}")
    print(f"USD Cost: {metrics.input_cost_usd + metrics.output_cost_usd}")
    print(f"SUCCESS: ScoringEngine logic is valid.")
    
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
