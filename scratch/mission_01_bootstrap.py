import os
import sys
import uuid
import logging
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.models.domain import (
    EnhancedThought, ThoughtMetrics, CCTSessionState, ThinkingStrategy, ThoughtType, CCTProfile
)
from src.engines.memory.manager import MemoryManager
from src.engines.memory.thinking_patterns import PatternArchiver
from src.engines.sequential.engine import SequentialEngine
from src.engines.sequential.models import SequentialContext

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def run_metacognitive_mission():
    logger.info("🚀 Starting Mission 01: Metacognitive Bootstrap")
    
    # 1. Initialize Components
    memory = MemoryManager()
    archiver = PatternArchiver(memory)
    
    session_id = f"MISSION_{uuid.uuid4().hex[:6].upper()}"
    problem = "Architecting the CCT Multi-Agent Fusion Orchestrator for Enterprise Scalability."
    
    session = CCTSessionState(
        session_id=session_id,
        problem_statement=problem,
        profile=CCTProfile.BALANCED,
        active_strategy=ThinkingStrategy.SYSTEMIC
    )
    
    sequential_context = SequentialContext(thought_number=1, session_id=session_id)
    
    # 2. Simulate Thought Flow
    
    # THOUGHT 1: DECONSTRUCTION (Not Golden)
    t1 = EnhancedThought(
        id=f"T_{uuid.uuid4().hex[:6]}",
        parent_id=None,
        strategy=ThinkingStrategy.ANALYTICAL,
        thought_type=ThoughtType.ANALYSIS,
        summary="Deconstruction of Fusion requirements.",
        content="""The Multi-Agent Fusion orchestrator requires a mechanism to handle conflicting personas. 
        Requirements:
        1. Specialized Personas (Architect, Auditor, Coder).
        2. Synthesis logic (Consensus vs. Majority).
        3. Token economy (Pruning irrelevant branches).""",
        sequential_context=sequential_context,
        metrics=ThoughtMetrics(
            logical_coherence=0.85,  # Below 0.9 threshold
            evidence_strength=0.75,
            novelty_score=0.6,
            depth_of_thought=0.7
        ),
        tags=["deconstruction", "requirements"]
    )
    
    # THOUGHT 2: THE CRUCIBLE (BATTLE-TESTED ARCHITECTURE) - PATTERN CANDIDATE
    t2 = EnhancedThought(
        id=f"T_{uuid.uuid4().hex[:6]}",
        parent_id=t1.id,
        strategy=ThinkingStrategy.INTEGRATIVE,
        thought_type=ThoughtType.SYNTHESIS,
        summary="Multi-Agent Consensus Pattern (The Arch-God Protocol)",
        content="""Proposed Architecture: 'Weighted Persona Consensus'
        
        1. **Expert War Room**: Each agent generates a local outcome.
        2. **Critical Cross-Examination**: Agents critique each other's outputs in a secondary primitive cycle.
        3. **Synthesis**: A 'Master Architect' persona performs a Weighted Sum reduction based on Confidence scores.
        4. **Conflict Resolution**: If consensus is < 0.7, trigger a 'Fundamental Rethink' (Reset context to anchor points).
        
        This pattern ensures that a low-confidence but critical insight (e.g., from a Security expert) isn't overruled by a high-confidence UI/UX agent.""",
        sequential_context=sequential_context,
        metrics=ThoughtMetrics(
            logical_coherence=0.98,  # ABOVE 0.9 threshold
            evidence_strength=0.92,  # ABOVE 0.8 threshold
            novelty_score=0.95,
            depth_of_thought=0.9
        ),
        tags=["architecture", "synthesis", "multi-agent"]
    )
    
    # 3. Process thoughts through Archiver
    logger.info("Processing thoughts for Thinking Pattern identification...")
    
    tp1 = archiver.process_thought(session, t1)
    if not tp1:
        logger.info("✅ Thought 1 correctly rejected (below thresholds).")
        
    tp2 = archiver.process_thought(session, t2)
    if tp2:
        logger.info(f"🏆 THINKING PATTERN SAVED: {tp2.id}")
        logger.info(f"   Summary: {tp2.summary[:50]}...")
        
    # 4. Verify Database
    patterns = memory.get_global_patterns()
    if any(p.id == tp2.id for p in patterns):
        logger.info("✅ SQLite Verification: Pattern exists in global repository.")
    else:
        logger.error("❌ SQLite Verification FAILED!")

    # 5. Verify Markdown
    topic_dir = os.path.join("docs/context-tree/Thinking-Patterns", t2.strategy.value.capitalize())
    md_path = os.path.join(topic_dir, f"{tp2.id}.md")
    if os.path.exists(md_path):
        logger.info(f"✅ Markdown Verification: File created at {md_path}")
    else:
        logger.error(f"❌ Markdown Verification FAILED at {md_path}")

if __name__ == "__main__":
    run_metacognitive_mission()
