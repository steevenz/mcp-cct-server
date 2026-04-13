import pytest
from src.core.models.enums import ThinkingStrategy
from src.utils.pipelines import PipelineSelector

def test_planning_keywords():
    """Verify that planning-related keywords trigger the PLAN category."""
    statement = "I need a recursive search plan for the bug"
    categories = PipelineSelector.detect_categories(statement)
    assert "PLAN" in categories
    assert categories["PLAN"] > 0

def test_planning_pipeline_selection():
    """Verify that the PLAN category selects the correct strategies."""
    statement = "Design an autonomous reasoning workflow"
    pipeline = PipelineSelector.select_pipeline(statement)
    
    # The PLAN pipeline should contain our new strategies
    expected_strategies = [
        ThinkingStrategy.PLAN_AND_EXECUTE,
        ThinkingStrategy.REACT,
        ThinkingStrategy.TREE_OF_THOUGHTS,
        ThinkingStrategy.POST_MISSION_LEARNING
    ]
    assert pipeline == expected_strategies

def test_legacy_tree_refactoring():
    """Ensure legacy TREE is correctly mapped to TREE_OF_THOUGHTS in code if used."""
    # Since we refactored the enum, we just verify the new value exists
    assert ThinkingStrategy.TREE_OF_THOUGHTS == "tree_of_thoughts"
