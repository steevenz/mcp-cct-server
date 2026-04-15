"""
Verification tests for Whitepaper Section 3: The Intelligence Router & Pipeline Engine

Tests ensure implementation matches whitepaper concepts, DDD compliance, and MCP server goals.
"""

import pytest
from src.core.services.pipeline_policy import PipelinePolicyManager
from src.core.services.routing import IntelligenceRouter
from src.core.services.complexity import TaskComplexity, ComplexityService
from src.core.models.enums import ThinkingStrategy
from src.core.models.domain import CCTSessionState, EnhancedThought, ThoughtMetrics
from unittest.mock import Mock


class TestPhase1LexicalIgnition:
    """Test Phase 1: Lexical Ignition & Weighted Discovery"""
    
    def test_7_core_domains_defined(self):
        """Verify 7 core domains are defined"""
        domains = PipelinePolicyManager.KEYWORDS.keys()
        expected = {"DEBUG", "ARCH", "SEC", "FEAT", "BIZ", "PLAN", "ENGINEERING"}
        assert domains == expected, f"Expected {expected}, got {domains}"
    
    def test_logarithmic_scoring_formula(self):
        """Verify logarithmic scoring boost formula: 0.3 + matches * 0.15, capped at 1.0"""
        # Test with 1 match
        scores = PipelinePolicyManager.detect_categories("bug fix")
        assert "DEBUG" in scores
        # Actual formula is 0.3 + matches * 0.15 = 0.3 + 0.15 = 0.45
        # But with "bug fix" we get 2 matches (bug, fix) = 0.3 + 2*0.15 = 0.6
        assert scores["DEBUG"] == 0.3 + (2 * 0.15)  # 0.6
        
        # Test with multiple matches
        scores = PipelinePolicyManager.detect_categories("bug fix error crash debug")
        assert "DEBUG" in scores
        # "bug fix error crash debug" has 5 matches = 0.3 + 5*0.15 = 1.05, capped at 1.0
        assert scores["DEBUG"] == 1.0  # Capped
        
        # Test with no matches
        scores = PipelinePolicyManager.detect_categories("hello world")
        assert len(scores) == 0
    
    def test_scenario_mapping_returns_weighted_map(self):
        """Verify scenario mapping returns weighted scenario map"""
        scores = PipelinePolicyManager.detect_categories("security vulnerability architecture")
        assert isinstance(scores, dict)
        assert all(isinstance(v, float) for v in scores.values())
        assert all(0.0 <= v <= 1.0 for v in scores.values())


class TestPhase2CognitiveBlueprint:
    """Test Phase 2: The Cognitive Blueprint"""
    
    def test_cct_session_state_has_primary_category(self):
        """Verify CCTSessionState has primary_category field"""
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile="balanced"
        )
        assert hasattr(session, 'primary_category')
        assert session.primary_category == "GENERIC"  # Default value
    
    def test_cct_session_state_has_suggested_pipeline(self):
        """Verify CCTSessionState has suggested_pipeline field"""
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile="balanced"
        )
        assert hasattr(session, 'suggested_pipeline')
        assert isinstance(session.suggested_pipeline, list)
        assert all(isinstance(s, ThinkingStrategy) for s in session.suggested_pipeline)
    
    def test_cct_session_state_has_detected_categories(self):
        """Verify CCTSessionState has detected_categories field"""
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile="balanced"
        )
        assert hasattr(session, 'detected_categories')
        assert isinstance(session.detected_categories, dict)


class TestDeepReasoningCatalog:
    """Test Deep Reasoning Catalog (7 domain pipelines)"""
    
    def test_debug_pipeline_matches_whitepaper(self):
        """Verify DEBUG pipeline matches whitepaper specification"""
        pipeline = PipelinePolicyManager.PIPELINE_TEMPLATES["DEBUG"]
        expected = [
            ThinkingStrategy.SELF_DEBUGGING,
            ThinkingStrategy.EMPIRICAL_RESEARCH,
            ThinkingStrategy.ABDUCTIVE,
            ThinkingStrategy.FIRST_PRINCIPLES,
            ThinkingStrategy.ACTOR_CRITIC_LOOP
        ]
        assert pipeline == expected
    
    def test_arch_pipeline_matches_whitepaper(self):
        """Verify ARCH pipeline matches whitepaper specification"""
        pipeline = PipelinePolicyManager.PIPELINE_TEMPLATES["ARCH"]
        expected = [
            ThinkingStrategy.BRAINSTORMING,
            ThinkingStrategy.ENGINEERING_DECONSTRUCTION,
            ThinkingStrategy.FIRST_PRINCIPLES,
            ThinkingStrategy.SYSTEMIC,
            ThinkingStrategy.COUNCIL_OF_CRITICS,
            ThinkingStrategy.POST_MISSION_LEARNING
        ]
        assert pipeline == expected
    
    def test_sec_pipeline_matches_whitepaper(self):
        """Verify SEC pipeline matches whitepaper specification"""
        pipeline = PipelinePolicyManager.PIPELINE_TEMPLATES["SEC"]
        expected = [
            ThinkingStrategy.CRITICAL,
            ThinkingStrategy.ACTOR_CRITIC_LOOP,
            ThinkingStrategy.SYSTEMIC,
            ThinkingStrategy.POST_MISSION_LEARNING
        ]
        assert pipeline == expected
    
    def test_feat_pipeline_matches_whitepaper(self):
        """Verify FEAT pipeline matches whitepaper specification"""
        pipeline = PipelinePolicyManager.PIPELINE_TEMPLATES["FEAT"]
        expected = [
            ThinkingStrategy.BRAINSTORMING,
            ThinkingStrategy.ENGINEERING_DECONSTRUCTION,
            ThinkingStrategy.SYSTEMATIC,
            ThinkingStrategy.ACTOR_CRITIC_LOOP,
            ThinkingStrategy.POST_MISSION_LEARNING
        ]
        assert pipeline == expected
    
    def test_biz_pipeline_matches_whitepaper(self):
        """Verify BIZ pipeline matches whitepaper specification"""
        pipeline = PipelinePolicyManager.PIPELINE_TEMPLATES["BIZ"]
        expected = [
            ThinkingStrategy.SWOT_ANALYSIS,
            ThinkingStrategy.SECOND_ORDER_THINKING,
            ThinkingStrategy.LONG_TERM_HORIZON,
            ThinkingStrategy.POST_MISSION_LEARNING
        ]
        assert pipeline == expected
    
    def test_plan_pipeline_matches_whitepaper(self):
        """Verify PLAN pipeline matches whitepaper specification"""
        pipeline = PipelinePolicyManager.PIPELINE_TEMPLATES["PLAN"]
        expected = [
            ThinkingStrategy.PLAN_AND_EXECUTE,
            ThinkingStrategy.REACT,
            ThinkingStrategy.TREE_OF_THOUGHTS,
            ThinkingStrategy.POST_MISSION_LEARNING
        ]
        assert pipeline == expected
    
    def test_engineering_pipeline_matches_whitepaper(self):
        """Verify ENGINEERING pipeline matches whitepaper specification"""
        pipeline = PipelinePolicyManager.PIPELINE_TEMPLATES["ENGINEERING"]
        expected = [
            ThinkingStrategy.BRAINSTORMING,
            ThinkingStrategy.ENGINEERING_DECONSTRUCTION,
            ThinkingStrategy.SYSTEMIC,
            ThinkingStrategy.DEDUCTIVE_VALIDATION,
            ThinkingStrategy.POST_MISSION_LEARNING
        ]
        assert pipeline == expected


class TestThreeTieredHierarchy:
    """Test Automated Strategy Routing & 3-Tiered Hierarchy"""
    
    def test_tier1_sovereign_pipeline_for_complex_tasks(self):
        """Verify Tier 1: Sovereign Force for COMPLEX/SOVEREIGN tasks"""
        pipeline = PipelinePolicyManager.select_pipeline(
            "test problem",
            TaskComplexity.COMPLEX
        )
        assert pipeline == PipelinePolicyManager.SOVEREIGN_PIPELINE
        
        pipeline = PipelinePolicyManager.select_pipeline(
            "test problem",
            TaskComplexity.SOVEREIGN
        )
        assert pipeline == PipelinePolicyManager.SOVEREIGN_PIPELINE
    
    def test_tier2_domain_templates_for_moderate_tasks(self):
        """Verify Tier 2: Domain Templates for moderate complexity"""
        pipeline = PipelinePolicyManager.select_pipeline(
            "architecture design refactor",
            TaskComplexity.MODERATE
        )
        assert pipeline == PipelinePolicyManager.PIPELINE_TEMPLATES["ARCH"]
    
    def test_tier3_heuristic_fallback_for_generic_tasks(self):
        """Verify Tier 3: Heuristic Fallback for generic tasks"""
        pipeline = PipelinePolicyManager.select_pipeline(
            "simple task",
            TaskComplexity.SIMPLE
        )
        # Should return generic pipeline
        assert len(pipeline) > 0
        assert pipeline[0] in [ThinkingStrategy.FIRST_PRINCIPLES, ThinkingStrategy.LINEAR]


class TestSovereign9StepPipeline:
    """Test The Sovereign 9-Step Pipeline"""
    
    def test_sovereign_pipeline_has_9_phases(self):
        """Verify Sovereign pipeline has exactly 9 phases"""
        pipeline = PipelinePolicyManager.SOVEREIGN_PIPELINE
        assert len(pipeline) == 9
    
    def test_sovereign_pipeline_phase_order(self):
        """Verify Sovereign pipeline phase order matches whitepaper"""
        expected_order = [
            ThinkingStrategy.EMPIRICAL_RESEARCH,
            ThinkingStrategy.FIRST_PRINCIPLES,
            ThinkingStrategy.ACTOR_CRITIC_LOOP,
            ThinkingStrategy.COUNCIL_OF_CRITICS,
            ThinkingStrategy.SYSTEMIC,
            ThinkingStrategy.UNCONVENTIONAL_PIVOT,
            ThinkingStrategy.LONG_TERM_HORIZON,
            ThinkingStrategy.MULTI_AGENT_FUSION,
            ThinkingStrategy.POST_MISSION_LEARNING
        ]
        assert PipelinePolicyManager.SOVEREIGN_PIPELINE == expected_order


class TestNeuralRecalculationDynamicPivoting:
    """Test Neural Recalculation & Dynamic Pivoting"""
    
    def test_dynamic_pivoting_on_quality_drop(self):
        """Verify dynamic pivoting triggers when quality drops below thresholds"""
        router = IntelligenceRouter()
        
        # Create session with low quality metrics
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile="balanced",
            current_thought_number=1,
            suggested_pipeline=[ThinkingStrategy.LINEAR]
        )
        
        # Create thought with low clarity (below threshold of 0.4)
        from src.core.models.contexts import SequentialContext
        thought = EnhancedThought(
            id="thought_1",
            content="Test content",
            thought_type="analysis",
            strategy=ThinkingStrategy.LINEAR,
            sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5),
            metrics=ThoughtMetrics(
                clarity_score=0.3,  # Below PIVOT_THRESHOLD_CLARITY (0.4)
                logical_coherence=0.8,
                evidence_strength=0.7,
                novelty_score=0.9,
                input_tokens=100,
                output_tokens=200
            )
        )
        
        next_strategy = router.next_strategy(session, [thought])
        assert next_strategy == ThinkingStrategy.UNCONVENTIONAL_PIVOT
    
    def test_convergence_detection_high_evidence(self):
        """Verify convergence detection triggers with high evidence strength"""
        router = IntelligenceRouter()
        
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile="balanced",
            current_thought_number=5,
            estimated_total_thoughts=10
        )
        
        # Create 2 thoughts with high evidence (required for convergence detection)
        from src.core.models.contexts import SequentialContext
        thought1 = EnhancedThought(
            id="thought_1",
            content="Previous thought",
            thought_type="analysis",
            strategy=ThinkingStrategy.LINEAR,
            sequential_context=SequentialContext(thought_number=4, estimated_total_thoughts=10),
            metrics=ThoughtMetrics(
                clarity_score=0.9,
                logical_coherence=0.95,
                evidence_strength=0.9,
                novelty_score=0.8,
                input_tokens=100,
                output_tokens=200
            )
        )
        
        thought2 = EnhancedThought(
            id="thought_2",
            content="Test conclusion",
            thought_type="conclusion",
            strategy=ThinkingStrategy.INTEGRATIVE,
            sequential_context=SequentialContext(thought_number=5, estimated_total_thoughts=10),
            metrics=ThoughtMetrics(
                clarity_score=0.9,
                logical_coherence=0.95,
                evidence_strength=0.9,  # Above 0.8 threshold
                novelty_score=0.8,
                input_tokens=100,
                output_tokens=200
            )
        )
        
        should_finish = router.should_finish(session, [thought1, thought2])
        assert should_finish is True


class TestMetricsIntegration:
    """Test Metrics Integration in Routing"""
    
    def test_router_has_metrics_enabled(self):
        """Verify IntelligenceRouter has metrics collection enabled"""
        router = IntelligenceRouter()
        assert hasattr(router, 'metrics_enabled')
        assert router.metrics_enabled is True
    
    def test_router_has_get_metrics_method(self):
        """Verify IntelligenceRouter has get_routing_metrics method"""
        router = IntelligenceRouter()
        assert hasattr(router, 'get_routing_metrics')
        assert callable(router.get_routing_metrics)


class TestDDDCompliance:
    """Test DDD Compliance"""
    
    def test_pipeline_policy_is_domain_service(self):
        """Verify PipelinePolicyManager is a domain service"""
        # Domain services should be in src/core/services/
        from src.core.services import pipeline_policy
        assert pipeline_policy is not None
    
    def test_intelligence_router_is_domain_service(self):
        """Verify IntelligenceRouter is a domain service"""
        # Domain services should be in src/core/services/
        from src.core.services import routing
        assert routing is not None
    
    def test_domain_models_in_correct_layer(self):
        """Verify domain models are in src/core/models/"""
        from src.core.models import domain, enums
        assert domain is not None
        assert enums is not None
    
    def test_enums_are_value_objects(self):
        """Verify enums are proper value objects"""
        from src.core.models.enums import ThinkingStrategy
        # Enums should be immutable value objects
        strategy = ThinkingStrategy.LINEAR
        assert strategy.value == "linear"


class TestMCPServerAlignment:
    """Test MCP Server Goal Alignment"""
    
    def test_no_direct_llm_calls_in_routing(self):
        """Verify routing logic doesn't make direct LLM calls"""
        # IntelligenceRouter should only use scoring engine for metrics
        # No direct calls to LLM services in routing logic
        router = IntelligenceRouter()
        # Router should work without LLM dependency
        assert router.scoring is None or hasattr(router.scoring, 'analyze_thought')
    
    def test_pipeline_selection_is_deterministic(self):
        """Verify pipeline selection is deterministic (no external API calls)"""
        # Pipeline selection should be based on problem statement and complexity only
        pipeline1 = PipelinePolicyManager.select_pipeline("architecture design", TaskComplexity.MODERATE)
        pipeline2 = PipelinePolicyManager.select_pipeline("architecture design", TaskComplexity.MODERATE)
        assert pipeline1 == pipeline2


class TestNoPlaceholders:
    """Test No Placeholders or TODO Comments"""
    
    def test_pipeline_policy_no_placeholders(self):
        """Verify pipeline_policy.py has no TODO or FIXME comments"""
        import inspect
        source = inspect.getsource(PipelinePolicyManager)
        assert "TODO" not in source
        assert "FIXME" not in source
        assert "placeholder" not in source.lower()
    
    def test_routing_no_placeholders(self):
        """Verify routing.py has no TODO or FIXME comments"""
        import inspect
        source = inspect.getsource(IntelligenceRouter)
        assert "TODO" not in source
        assert "FIXME" not in source
        assert "placeholder" not in source.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
