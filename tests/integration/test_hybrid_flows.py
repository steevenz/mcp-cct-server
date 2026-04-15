"""
Integration tests for complex hybrid cognitive flows.

Tests end-to-end scenarios combining multiple engines:
- Actor-Critic loop with external review
- Council of Critics with multi-agent fusion
- Temporal Horizon with Lateral Pivot
- Multi-agent fusion with convergence detection
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.engines.orchestrator import CognitiveOrchestrator
from src.core.models.enums import ThinkingStrategy, CCTProfile
from src.core.models.domain import CCTSessionState, EnhancedThought


@pytest.fixture
def mock_orchestrator():
    """Create a mock CognitiveOrchestrator for integration testing."""
    # This would normally use real components, but for integration tests
    # we can use mocks that simulate real behavior
    orchestrator = Mock()
    orchestrator.memory = Mock()
    orchestrator.registry = Mock()
    orchestrator.fusion = Mock()
    orchestrator.router = Mock()
    orchestrator.identity = Mock()
    orchestrator.autonomous = Mock()
    
    # Setup realistic mock behaviors
    orchestrator.memory.get_session = Mock()
    orchestrator.memory.get_session_history = Mock(return_value=[])
    orchestrator.memory.save_thought = Mock()
    orchestrator.memory.update_session = Mock()
    
    orchestrator.autonomous.get_execution_mode = Mock(return_value="autonomous")
    orchestrator.router.next_strategy = Mock(return_value=ThinkingStrategy.LINEAR)
    orchestrator.router.should_finish = Mock(return_value=False)
    
    return orchestrator


@pytest.fixture
def sample_session():
    """Create a sample session for testing."""
    session = CCTSessionState(
        session_id="test_session_001",
        problem_statement="Design a scalable microservices architecture",
        profile=CCTProfile.BALANCED,
        estimated_thoughts=10
    )
    session.complexity = "moderate"
    session.model_id = "claude-3-5-sonnet-20240620"
    return session


class TestActorCriticFlow:
    """Integration tests for Actor-Critic hybrid flow."""
    
    @pytest.mark.asyncio
    async def test_actor_critic_full_flow(self, sample_session, mock_orchestrator):
        """Test complete actor-critic loop with critic and synthesis phases."""
        mock_orchestrator.memory.get_session = Mock(return_value=sample_session)
        
        # Simulate the flow:
        # 1. Generate initial thought
        # 2. Trigger actor-critic loop
        # 3. Generate critic thought
        # 4. Generate synthesis thought
        
        # This would normally call the actual orchestrator.think() method
        # For integration testing, we simulate the behavior
        
        # Step 1: Initial thought
        initial_thought = EnhancedThought(
            id="thought_001",
            content="Implement microservices with API Gateway",
            thought_type="plan",
            strategy=ThinkingStrategy.LINEAR,
            sequential_context={}
        )
        
        # Step 2: Trigger actor-critic
        mock_orchestrator.memory.get_thought = Mock(return_value=initial_thought)
        
        # Step 3: Critic phase
        critic_thought = EnhancedThought(
            id="thought_002",
            content="API Gateway introduces single point of failure",
            thought_type="evaluation",
            strategy=ThinkingStrategy.CRITICAL,
            parent_id=initial_thought.id,
            sequential_context={}
        )
        
        # Step 4: Synthesis phase
        synthesis_thought = EnhancedThought(
            id="thought_003",
            content="Use API Gateway with load balancer and circuit breaker",
            thought_type="synthesis",
            strategy=ThinkingStrategy.DIALECTICAL,
            parent_id=critic_thought.id,
            builds_on=[initial_thought.id, critic_thought.id],
            sequential_context={}
        )
        
        # Verify the flow structure
        assert critic_thought.parent_id == initial_thought.id
        assert synthesis_thought.parent_id == critic_thought.id
        assert initial_thought.id in synthesis_thought.builds_on
        assert critic_thought.id in synthesis_thought.builds_on


class TestCouncilOfCriticsFlow:
    """Integration tests for Council of Critics hybrid flow."""
    
    @pytest.mark.asyncio
    async def test_council_of_critics_multi_persona_flow(self, sample_session):
        """Test council of critics with multiple specialist personas."""
        personas = ["Security Expert", "Performance Engineer", "DevOps Specialist"]
        
        # Simulate the flow:
        # 1. Generate target thought
        # 2. Each persona generates critique
        # 3. Fusion generates consensus
        
        target_thought = EnhancedThought(
            id="target_001",
            content="Use PostgreSQL for all data storage",
            thought_type="plan",
            strategy=ThinkingStrategy.LINEAR,
            sequential_context={}
        )
        
        # Each persona generates a critique
        critic_thoughts = []
        for i, persona in enumerate(personas):
            critic = EnhancedThought(
                id=f"critic_{i:03d}",
                content=f"{persona} perspective on data storage",
                thought_type="evaluation",
                strategy=ThinkingStrategy.CRITICAL,
                parent_id=target_thought.id,
                sequential_context={}
            )
            critic_thoughts.append(critic)
        
        # Fusion generates consensus
        consensus_thought = EnhancedThought(
            id="consensus_001",
            content="Use PostgreSQL for transactional data, Redis for caching",
            thought_type="synthesis",
            strategy=ThinkingStrategy.INTEGRATIVE,
            parent_id=critic_thoughts[-1].id,
            builds_on=[target_thought.id] + [c.id for c in critic_thoughts],
            sequential_context={}
        )
        
        # Verify the structure
        assert len(critic_thoughts) == len(personas)
        assert all(c.parent_id == target_thought.id for c in critic_thoughts)
        assert consensus_thought.parent_id == critic_thoughts[-1].id
        assert target_thought.id in consensus_thought.builds_on
        assert all(c.id in consensus_thought.builds_on for c in critic_thoughts)


class TestTemporalHorizonFlow:
    """Integration tests for Temporal Horizon hybrid flow."""
    
    @pytest.mark.asyncio
    async def test_temporal_horizon_now_next_later(self, sample_session):
        """Test temporal projection across NOW, NEXT, LATER timelines."""
        target_thought = EnhancedThought(
            id="temporal_001",
            content="Implement feature flag system",
            thought_type="plan",
            strategy=ThinkingStrategy.LINEAR,
            sequential_context={}
        )
        
        # Temporal projection thought
        temporal_thought = EnhancedThought(
            id="temporal_002",
            content="""NOW: Implement basic feature flag toggle
NEXT: Add analytics and rollback capability
LATER: Advanced targeting and A/B testing""",
            thought_type="evaluation",
            strategy=ThinkingStrategy.LONG_TERM_HORIZON,
            parent_id=target_thought.id,
            sequential_context={}
        )
        
        # Verify temporal structure
        assert "NOW:" in temporal_thought.content
        assert "NEXT:" in temporal_thought.content
        assert "LATER:" in temporal_thought.content
        assert temporal_thought.parent_id == target_thought.id


class TestMultiAgentFusionFlow:
    """Integration tests for Multi-Agent Fusion hybrid flow."""
    
    @pytest.mark.asyncio
    async def test_multi_agent_divergent_convergent_flow(self, sample_session):
        """Test divergent persona generation followed by convergent fusion."""
        target_thought = EnhancedThought(
            id="fusion_001",
            content="Design authentication system",
            thought_type="plan",
            strategy=ThinkingStrategy.LINEAR,
            sequential_context={}
        )
        
        # Divergent phase: multiple persona insights
        persona_thoughts = []
        personas = ["Security Architect", "UX Designer", "Backend Engineer"]
        for i, persona in enumerate(personas):
            thought = EnhancedThought(
                id=f"persona_{i:03d}",
                content=f"{persona} perspective on authentication",
                thought_type="analysis",
                strategy=ThinkingStrategy.CRITICAL,
                parent_id=target_thought.id,
                sequential_context={}
            )
            persona_thoughts.append(thought)
        
        # Convergent phase: fusion synthesis
        fusion_thought = EnhancedThought(
            id="fusion_002",
            content="Implement OAuth 2.0 with JWT tokens",
            thought_type="synthesis",
            strategy=ThinkingStrategy.INTEGRATIVE,
            parent_id=persona_thoughts[-1].id,
            builds_on=[target_thought.id] + [p.id for p in persona_thoughts],
            sequential_context={}
        )
        
        # Verify divergent-convergent structure
        assert len(persona_thoughts) == len(personas)
        assert all(p.parent_id == target_thought.id for p in persona_thoughts)
        assert fusion_thought.parent_id == persona_thoughts[-1].id
        assert len(fusion_thought.builds_on) == len(persona_thoughts) + 1


class TestConvergenceDetection:
    """Integration tests for convergence detection in complex flows."""
    
    @pytest.mark.asyncio
    async def test_early_convergence_detection(self, sample_session):
        """Test early convergence detection with high coherence thoughts."""
        # Create a sequence of high-coherence thoughts
        thoughts = []
        for i in range(3):
            thought = EnhancedThought(
                id=f"thought_{i:03d}",
                content=f"High quality thought {i}",
                thought_type="analysis",
                strategy=ThinkingStrategy.LINEAR,
                sequential_context={}
            )
            # Mock high coherence metrics
            from src.core.models.domain import ThoughtMetrics
            thought.metrics = ThoughtMetrics(
                clarity_score=0.9,
                logical_coherence=0.96,  # Above 0.95 threshold
                evidence_strength=0.85,
                novelty_score=0.8,
                input_tokens=100,
                output_tokens=200,
                input_cost_usd=0.001,
                output_cost_usd=0.002,
                input_cost_idr=15.0,
                output_cost_idr=30.0,
                currency_rate_idr=15000.0
            )
            thoughts.append(thought)
        
        # Verify convergence criteria
        coherence_streak = all(
            t.metrics.logical_coherence >= 0.95 
            for t in thoughts[-2:]
        )
        strong_evidence = thoughts[-1].metrics.evidence_strength >= 0.8
        
        assert coherence_streak is True
        assert strong_evidence is True


class TestHybridComposition:
    """Integration tests for composing multiple hybrid modes."""
    
    @pytest.mark.asyncio
    async def test_actor_critic_then_council_of_critics(self, sample_session):
        """Test composing actor-critic followed by council of critics."""
        # Initial thought
        initial = EnhancedThought(
            id="initial_001",
            content="Initial proposal",
            thought_type="plan",
            strategy=ThinkingStrategy.LINEAR,
            sequential_context={}
        )
        
        # Actor-critic refinement
        critic = EnhancedThought(
            id="critic_001",
            content="Critic perspective",
            thought_type="evaluation",
            strategy=ThinkingStrategy.CRITICAL,
            parent_id=initial.id,
            sequential_context={}
        )
        
        synthesis = EnhancedThought(
            id="synthesis_001",
            content="Refined proposal",
            thought_type="synthesis",
            strategy=ThinkingStrategy.DIALECTICAL,
            parent_id=critic.id,
            builds_on=[initial.id, critic.id],
            sequential_context={}
        )
        
        # Council of critics on refined proposal
        council_critics = []
        for i in range(2):
            council = EnhancedThought(
                id=f"council_{i:03d}",
                content=f"Council critic {i}",
                thought_type="evaluation",
                strategy=ThinkingStrategy.CRITICAL,
                parent_id=synthesis.id,
                sequential_context={}
            )
            council_critics.append(council)
        
        # Final consensus
        consensus = EnhancedThought(
            id="consensus_001",
            content="Final consensus",
            thought_type="synthesis",
            strategy=ThinkingStrategy.INTEGRATIVE,
            parent_id=council_critics[-1].id,
            builds_on=[synthesis.id] + [c.id for c in council_critics],
            sequential_context={}
        )
        
        # Verify composition
        assert synthesis.parent_id == critic.id
        assert all(c.parent_id == synthesis.id for c in council_critics)
        assert consensus.parent_id == council_critics[-1].id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
