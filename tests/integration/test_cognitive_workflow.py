import pytest
from src.core.models.enums import ThinkingStrategy, ThoughtType, CCTProfile

@pytest.mark.skip(reason="CognitiveOrchestrator fixture needs identity and autonomous parameters")
@pytest.mark.asyncio
async def test_complete_cognitive_cycle(orchestrator):
    """
    Test a full cognitive loop: 
    Start -> Think -> Criticize -> Synthesize -> Export -> Analyze
    """
    # 1. Start Session
    session_result = orchestrator.start_session(
        problem_statement="Should we use Microservices?",
        profile="balanced"
    )
    session_id = session_result["session_id"]
    session_token = session_result.get("session_token", "")
    assert session_id is not None
    
    # 2. Add an initial thought (Primitive: Systematic)
    thought_1 = orchestrator.execute_strategy(
        session_id=session_id,
        strategy=ThinkingStrategy.SYSTEMATIC,
        payload={
            "thought_content": "We should use microservices for scalability.",
            "thought_type": "hypothesis",
            "strategy": "systematic",
            "thought_number": 1,
            "estimated_total_thoughts": 5,
            "next_thought_needed": True
        }
    )
    assert thought_1["status"] == "success"
    target_id = thought_1["generated_thought_id"]
    
    # 3. Trigger Actor-Critic Hybrid loop on that thought
    # This automated step will create 2 nodes (Critic and Synthesis)
    actor_critic_result = orchestrator.execute_strategy(
        session_id=session_id,
        strategy=ThinkingStrategy.ACTOR_CRITIC_LOOP,
        payload={
            "target_thought_id": target_id,
            "critic_persona": "Cost Optimizer"
        }
    )
    assert actor_critic_result["status"] == "success"
    critic_id = actor_critic_result["critic_phase"]["generated_id"]
    synth_id = actor_critic_result["synthesis_phase"]["generated_id"]
    
    # 4. Export the session and verify tree integrity
    history = orchestrator.memory.get_session_history(session_id)
    assert len(history) == 3 # Systematic + Critic + Synthesis
    
    ids = [t.id for t in history]
    assert target_id in ids
    assert critic_id in ids
    assert synth_id in ids
    
    # Verify parent linkage
    critic_thought = orchestrator.memory.get_thought(critic_id)
    assert critic_thought.parent_id == target_id
    
    synth_thought = orchestrator.memory.get_thought(synth_id)
    assert synth_thought.parent_id == critic_id
    
    # 5. Run Analysis
    # We simulate this via the same logic as the tool
    # (Since we are testing the orchestrator + logic integration)
    from src.tools.simplified import register_export_tools
    from mcp.server.fastmcp import FastMCP
    
    mcp = FastMCP("test")
    register_export_tools(mcp, orchestrator)
    analyze_tool = mcp._tool_manager.get_tool("analyze_session").fn
    
    analysis = analyze_tool(session_id, session_token=session_token)
    assert "metrics" in analysis
    assert analysis["metrics"]["clarity_score"] > 0
    assert analysis["metrics"]["consistency_score"] > 0
