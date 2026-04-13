import logging
import asyncio
from typing import Dict, Any

# Mocking parts of the system for standalone testing of the logic in simplified_tools and pipelines
from src.core.models.enums import ThinkingStrategy
from src.tools.simplified_tools import TaskComplexity
from src.utils.pipelines import PipelineSelector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VERIFY")

def test_pipeline_selection():
    """Verifies that multi-scenario detection and Sovereign pipeline selection work correctly."""
    # Scenario: Architecture + Security (Multi-Domain)
    problem = "We need to refactor our system architecture to harden it against SQL injection vulnerabilities."
    
    # 1. Test Weighted Category Detection
    categories = PipelineSelector.detect_categories(problem)
    logger.info(f"Detected Categories: {categories}")
    assert "ARCH" in categories
    assert "SEC" in categories
    
    primary = PipelineSelector.detect_category(problem)
    logger.info(f"Primary Category: {primary}")
    assert primary == "ARCH" # 'refactor' appears before 'injection' or just higher weight
    
    # 2. Test Persona Selection
    personas = PipelineSelector.get_personas_for_domains(categories)
    logger.info(f"Council Personas: {personas}")
    assert "System Architect" in personas
    assert "Security Auditor" in personas
    
    # 3. Test Sovereign Pipeline Selection
    # Forcing complexity complex manually for this test assertion
    pipeline = PipelineSelector.select_pipeline(problem, complexity="complex")
    logger.info(f"Sovereign Pipeline (8 steps): {[s.value for s in pipeline]}")
    assert len(pipeline) == 8
    assert pipeline[2] == ThinkingStrategy.ACTOR_CRITIC_LOOP
    assert pipeline[3] == ThinkingStrategy.COUNCIL_OF_CRITICS

if __name__ == "__main__":
    test_pipeline_selection()
    print("\n[SUCCESS] Pipeline logic verified.")
