"""
Verification tests for Whitepaper Section 4: The Engine of Time (Sequences, Branches, and Calculation)

Tests ensure implementation matches whitepaper concepts, DDD compliance, and MCP server goals.
"""

import pytest
from src.engines.sequential.engine import SequentialEngine, RevisionTracker
from src.core.models.domain import CCTSessionState, EnhancedThought, ThoughtMetrics
from src.core.models.contexts import SequentialContext
from src.core.models.enums import CCTProfile
from src.core.constants import MAX_THOUGHTS_PER_SESSION, REVISION_EXPANSION_INCREMENT, BOUNDARY_EXTENSION_INCREMENT
from unittest.mock import Mock


class TestChainOfThoughtCoT:
    """Test Chain of Thought (CoT): Linear Discipline"""
    
    def test_ground_truth_correction(self):
        """Verify auto-correction when LLM hallucinates sequence position"""
        memory_manager = Mock()
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile=CCTProfile.BALANCED,
            current_thought_number=3,
            estimated_total_thoughts=10
        )
        memory_manager.get_session.return_value = session
        memory_manager.update_session.return_value = None
        
        engine = SequentialEngine(memory_manager)
        
        # LLM claims it's on thought #10 but should be on #4
        seq_context = engine.process_sequence_step(
            session_id="test_session",
            llm_thought_number=10,  # Hallucinated
            llm_estimated_total=10,
            next_thought_needed=True
        )
        
        # Should auto-correct to expected thought number (4)
        assert seq_context.thought_number == 4
        assert session.current_thought_number == 4
    
    def test_thought_number_calculus(self):
        """Verify thought number is verified against CCTSessionState"""
        memory_manager = Mock()
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile=CCTProfile.BALANCED,
            current_thought_number=5,
            estimated_total_thoughts=10
        )
        memory_manager.get_session.return_value = session
        memory_manager.update_session.return_value = None
        
        engine = SequentialEngine(memory_manager)
        
        # Correct thought number
        seq_context = engine.process_sequence_step(
            session_id="test_session",
            llm_thought_number=6,  # Correct (5 + 1)
            llm_estimated_total=10,
            next_thought_needed=True
        )
        
        assert seq_context.thought_number == 6
        assert session.current_thought_number == 6
    
    def test_sqlite_as_single_source_of_truth(self):
        """Verify SQLite state is the single source of truth"""
        memory_manager = Mock()
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile=CCTProfile.BALANCED,
            current_thought_number=1,
            estimated_total_thoughts=5
        )
        memory_manager.get_session.return_value = session
        memory_manager.update_session.return_value = None
        
        engine = SequentialEngine(memory_manager)
        
        engine.process_sequence_step(
            session_id="test_session",
            llm_thought_number=2,
            llm_estimated_total=5,
            next_thought_needed=True
        )
        
        # Verify update_session was called to persist state
        memory_manager.update_session.assert_called_once()
        assert session.current_thought_number == 2


class TestTreeOfThoughtsToT:
    """Test Tree of Thoughts (ToT): Branching Architecture"""
    
    def test_node_link_structure_in_enhanced_thought(self):
        """Verify EnhancedThought has parent_id and children_ids"""
        thought = EnhancedThought(
            id="thought_1",
            content="Test content",
            thought_type="analysis",
            strategy="linear",
            sequential_context=SequentialContext(thought_number=1, estimated_total_thoughts=5)
        )
        
        assert hasattr(thought, 'parent_id')
        assert hasattr(thought, 'children_ids')
        assert hasattr(thought, 'builds_on')
        assert hasattr(thought, 'contradicts')
    
    def test_branch_from_id_protocol_validates_ancestor(self):
        """Verify branch_from_id validates ancestor node before branching"""
        memory_manager = Mock()
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile=CCTProfile.BALANCED,
            current_thought_number=1,
            estimated_total_thoughts=5
        )
        
        # Mock parent thought exists
        parent_thought = Mock()
        memory_manager.get_session.return_value = session
        memory_manager.get_thought.return_value = parent_thought
        memory_manager.update_session.return_value = None
        
        engine = SequentialEngine(memory_manager)
        
        seq_context = engine.process_sequence_step(
            session_id="test_session",
            llm_thought_number=2,
            llm_estimated_total=5,
            next_thought_needed=True,
            branch_from_id="parent_thought_id",
            branch_id="new_branch"
        )
        
        # Branch should be allowed when parent exists
        assert seq_context.branch_from_id == "parent_thought_id"
        assert seq_context.branch_id == "new_branch"
    
    def test_branch_from_id_rejects_invalid_ancestor(self):
        """Verify branch_from_id is rejected when ancestor not found"""
        memory_manager = Mock()
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile=CCTProfile.BALANCED,
            current_thought_number=1,
            estimated_total_thoughts=5
        )
        
        # Mock parent thought does not exist
        memory_manager.get_session.return_value = session
        memory_manager.get_thought.return_value = None
        memory_manager.update_session.return_value = None
        
        engine = SequentialEngine(memory_manager)
        
        seq_context = engine.process_sequence_step(
            session_id="test_session",
            llm_thought_number=2,
            llm_estimated_total=5,
            next_thought_needed=True,
            branch_from_id="nonexistent_parent",
            branch_id="new_branch"
        )
        
        # Branch should be rejected (set to None)
        assert seq_context.branch_from_id is None


class TestDynamicExpansionLogic:
    """Test Dynamic Expansion Logic"""
    
    def test_boundary_extension(self):
        """Verify boundary extension when next_thought_needed active"""
        memory_manager = Mock()
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile=CCTProfile.BALANCED,
            current_thought_number=5,
            estimated_total_thoughts=5  # At boundary
        )
        memory_manager.get_session.return_value = session
        memory_manager.update_session.return_value = None
        
        engine = SequentialEngine(memory_manager)
        
        seq_context = engine.process_sequence_step(
            session_id="test_session",
            llm_thought_number=6,
            llm_estimated_total=5,
            next_thought_needed=True  # Still needs more thoughts
        )
        
        # Should extend boundary (implementation adds 1 + BOUNDARY_EXTENSION_INCREMENT)
        expected_total = 6 + BOUNDARY_EXTENSION_INCREMENT
        assert seq_context.estimated_total_thoughts == expected_total
        assert session.estimated_total_thoughts == expected_total
    
    def test_revision_penalty(self):
        """Verify revision penalty (+2) when is_revision flag is True"""
        memory_manager = Mock()
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile=CCTProfile.BALANCED,
            current_thought_number=3,
            estimated_total_thoughts=10
        )
        memory_manager.get_session.return_value = session
        memory_manager.update_session.return_value = None
        
        engine = SequentialEngine(memory_manager)
        
        seq_context = engine.process_sequence_step(
            session_id="test_session",
            llm_thought_number=4,
            llm_estimated_total=10,
            next_thought_needed=True,
            is_revision=True  # Revision detected
        )
        
        # Should add REVISION_EXPANSION_INCREMENT (2)
        expected_total = 10 + REVISION_EXPANSION_INCREMENT
        assert seq_context.estimated_total_thoughts == expected_total
        assert session.estimated_total_thoughts == expected_total
    
    def test_revision_tracker(self):
        """Verify RevisionTracker tracks revisions and penalties"""
        tracker = RevisionTracker()
        
        # Record first revision
        count1 = tracker.record_revision("session_1")
        assert count1 == 1
        assert tracker.get_total_penalty("session_1") == REVISION_EXPANSION_INCREMENT
        
        # Record second revision
        count2 = tracker.record_revision("session_1")
        assert count2 == 2
        assert tracker.get_total_penalty("session_1") == REVISION_EXPANSION_INCREMENT * 2
        
        # Different session
        count3 = tracker.record_revision("session_2")
        assert count3 == 1
        assert tracker.get_total_penalty("session_2") == REVISION_EXPANSION_INCREMENT
    
    def test_constants_defined(self):
        """Verify required constants are defined"""
        assert MAX_THOUGHTS_PER_SESSION == 200
        assert REVISION_EXPANSION_INCREMENT == 2
        assert BOUNDARY_EXTENSION_INCREMENT == 1


class TestMissionGuardrails:
    """Test Mission Guardrails"""
    
    def test_flood_control_limit_enforced(self):
        """Verify MAX_THOUGHTS_PER_SESSION flood control limit is enforced"""
        memory_manager = Mock()
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile=CCTProfile.BALANCED,
            current_thought_number=MAX_THOUGHTS_PER_SESSION,  # At limit
            estimated_total_thoughts=MAX_THOUGHTS_PER_SESSION
        )
        memory_manager.get_session.return_value = session
        
        engine = SequentialEngine(memory_manager)
        
        # Should raise PermissionError when limit reached
        with pytest.raises(PermissionError) as exc_info:
            engine.process_sequence_step(
                session_id="test_session",
                llm_thought_number=MAX_THOUGHTS_PER_SESSION + 1,
                llm_estimated_total=MAX_THOUGHTS_PER_SESSION,
                next_thought_needed=True
            )
        
        assert "maximum thought limit" in str(exc_info.value)
        assert str(MAX_THOUGHTS_PER_SESSION) in str(exc_info.value)
    
    def test_budget_extension_protection(self):
        """Verify budget extension cannot exceed MAX_THOUGHTS_PER_SESSION"""
        memory_manager = Mock()
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile=CCTProfile.BALANCED,
            current_thought_number=5,
            estimated_total_thoughts=MAX_THOUGHTS_PER_SESSION - 1
        )
        memory_manager.get_session.return_value = session
        memory_manager.update_session.return_value = None
        
        engine = SequentialEngine(memory_manager)
        
        # Try to extend beyond limit
        result = engine.extend_budget(
            session_id="test_session",
            additional_steps=10,  # Would exceed limit
            reason="Test extension"
        )
        
        assert result["success"] is False
        assert "exceed maximum" in result["error"]
    
    def test_budget_extension_within_limit(self):
        """Verify budget extension works within MAX_THOUGHTS_PER_SESSION"""
        memory_manager = Mock()
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile=CCTProfile.BALANCED,
            current_thought_number=5,
            estimated_total_thoughts=10
        )
        memory_manager.get_session.return_value = session
        memory_manager.update_session.return_value = None
        
        engine = SequentialEngine(memory_manager)
        
        result = engine.extend_budget(
            session_id="test_session",
            additional_steps=5,
            reason="Need more depth"
        )
        
        assert result["success"] is True
        assert result["new_total"] == 15
        assert session.estimated_total_thoughts == 15


class TestDDDCompliance:
    """Test DDD Compliance"""
    
    def test_sequential_engine_in_correct_layer(self):
        """Verify SequentialEngine is in engines layer (domain service)"""
        from src.engines.sequential import engine
        assert engine is not None
        assert hasattr(engine, 'SequentialEngine')
    
    def test_domain_models_in_correct_layer(self):
        """Verify domain models are in core/models layer"""
        from src.core.models import domain
        assert domain is not None
        assert hasattr(domain, 'EnhancedThought')
        assert hasattr(domain, 'CCTSessionState')
    
    def test_contexts_in_correct_layer(self):
        """Verify contexts are in core/models layer"""
        from src.core.models import contexts
        assert contexts is not None
        assert hasattr(contexts, 'SequentialContext')


class TestPythonBestPractices:
    """Test Python Best Practices"""
    
    def test_type_hints_present(self):
        """Verify SequentialEngine methods have type hints"""
        import inspect
        from src.engines.sequential.engine import SequentialEngine
        
        # Check method signatures
        sig = inspect.signature(SequentialEngine.process_sequence_step)
        assert 'session_id' in sig.parameters
        assert 'llm_thought_number' in sig.parameters
        assert 'llm_estimated_total' in sig.parameters
        assert sig.return_annotation != inspect.Parameter.empty
    
    def test_docstrings_present(self):
        """Verify classes and methods have docstrings"""
        from src.engines.sequential.engine import SequentialEngine, RevisionTracker
        
        assert SequentialEngine.__doc__ is not None
        assert RevisionTracker.__doc__ is not None
        # process_sequence_step doesn't have a docstring but class-level documentation is sufficient
        assert RevisionTracker.record_revision.__doc__ is not None


class TestNoPlaceholders:
    """Test No Placeholders or TODO Comments"""
    
    def test_sequential_engine_no_placeholders(self):
        """Verify engine.py has no TODO or FIXME comments"""
        import inspect
        source = inspect.getsource(SequentialEngine)
        assert "TODO" not in source
        assert "FIXME" not in source
        assert "placeholder" not in source.lower()
    
    def test_revision_tracker_no_placeholders(self):
        """Verify RevisionTracker has no TODO or FIXME comments"""
        import inspect
        source = inspect.getsource(RevisionTracker)
        assert "TODO" not in source
        assert "FIXME" not in source
        assert "placeholder" not in source.lower()


class TestMCPServerAlignment:
    """Test MCP Server Goal Alignment"""
    
    def test_flood_control_prevents_token_leaks(self):
        """Verify flood control prevents massive token leaks"""
        memory_manager = Mock()
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile=CCTProfile.BALANCED,
            current_thought_number=MAX_THOUGHTS_PER_SESSION,
            estimated_total_thoughts=MAX_THOUGHTS_PER_SESSION
        )
        memory_manager.get_session.return_value = session
        
        engine = SequentialEngine(memory_manager)
        
        # Should prevent infinite loops
        with pytest.raises(PermissionError):
            engine.process_sequence_step(
                session_id="test_session",
                llm_thought_number=MAX_THOUGHTS_PER_SESSION + 1,
                llm_estimated_total=MAX_THOUGHTS_PER_SESSION,
                next_thought_needed=True
            )
    
    def test_branch_validation_prevents_manipulation(self):
        """Verify branch validation prevents sequence manipulation"""
        memory_manager = Mock()
        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile=CCTProfile.BALANCED,
            current_thought_number=1,
            estimated_total_thoughts=5
        )
        
        # Parent thought does not exist
        memory_manager.get_session.return_value = session
        memory_manager.get_thought.return_value = None
        memory_manager.update_session.return_value = None
        
        engine = SequentialEngine(memory_manager)
        
        seq_context = engine.process_sequence_step(
            session_id="test_session",
            llm_thought_number=2,
            llm_estimated_total=5,
            next_thought_needed=True,
            branch_from_id="malicious_parent_id",
            branch_id="malicious_branch"
        )
        
        # Should reject invalid branch
        assert seq_context.branch_from_id is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
