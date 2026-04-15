"""
ToT Engine: Tree of Thoughts Pattern Implementation

Implements the Tree of Thoughts (ToT) pattern for branching exploration.
This pattern explores multiple reasoning paths simultaneously.

Reference: docs/context-tree/Planning/Patterns/TreeOfThoughts.md
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ThoughtNode:
    """A node in the thought tree."""
    id: str
    thought: str
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    score: float = 0.0
    depth: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "thought": self.thought,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "score": self.score,
            "depth": self.depth
        }


class ToTEngine:
    """
    Tree of Thoughts (ToT) Engine for branching exploration.
    
    Implements branching exploration of multiple reasoning paths:
    1. Generate multiple candidate thoughts
    2. Evaluate each thought
    3. Expand promising branches
    4. Prune low-quality branches
    5. Select best path
    """
    
    def __init__(self, max_depth: int = 3, branch_factor: int = 3):
        self.max_depth = max_depth
        self.branch_factor = branch_factor
        self._nodes: Dict[str, ThoughtNode] = {}
        self._node_counter = 0
    
    def process(
        self,
        problem: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a problem using ToT pattern.
        
        Args:
            problem: The problem to solve
            context: Current context and state
            
        Returns:
            Result with thought tree and best path
        """
        logger.info(f"[TOT] Starting ToT processing for: {problem[:50]}...")
        
        self._nodes = {}
        self._node_counter = 0
        
        # Generate root thought
        root_node = self._create_node(
            thought=f"Initial analysis of: {problem}",
            parent_id=None,
            depth=0
        )
        
        # Expand tree
        self._expand_tree(root_node, problem, context, 0)
        
        # Find best path
        best_path = self._find_best_path(root_node)
        
        return {
            "status": "success",
            "total_nodes": len(self._nodes),
            "max_depth": max(node.depth for node in self._nodes.values()),
            "best_path": best_path,
            "thought_tree": {node_id: node.to_dict() for node_id, node in self._nodes.items()},
            "pattern": "tree_of_thoughts"
        }
    
    def _create_node(
        self,
        thought: str,
        parent_id: Optional[str],
        depth: int
    ) -> ThoughtNode:
        """Create a new thought node."""
        node_id = f"node_{self._node_counter}"
        self._node_counter += 1
        
        node = ThoughtNode(
            id=node_id,
            thought=thought,
            parent_id=parent_id,
            depth=depth
        )
        self._nodes[node_id] = node
        
        # Link to parent
        if parent_id and parent_id in self._nodes:
            self._nodes[parent_id].children_ids.append(node_id)
        
        return node
    
    def _expand_tree(
        self,
        node: ThoughtNode,
        problem: str,
        context: Dict[str, Any],
        current_depth: int
    ):
        """Expand tree from a node."""
        if current_depth >= self.max_depth:
            return
        
        # Generate candidate thoughts
        candidates = self._generate_candidates(node.thought, problem, context)
        
        # Create child nodes for top candidates
        for i, candidate in enumerate(candidates[:self.branch_factor]):
            child_node = self._create_node(
                thought=candidate,
                parent_id=node.id,
                depth=current_depth + 1
            )
            
            # Score the thought
            child_node.score = self._score_thought(candidate, context)
            
            # Recursively expand if score is high enough
            if child_node.score > 0.5:
                self._expand_tree(child_node, problem, context, current_depth + 1)
    
    def _generate_candidates(
        self,
        parent_thought: str,
        problem: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """Generate candidate thoughts."""
        # Simple heuristic generation
        candidates = [
            f"Alternative approach to: {parent_thought}",
            f"Refinement of: {parent_thought}",
            f"Critical analysis of: {parent_thought}",
            f"Creative pivot from: {parent_thought}"
        ]
        return candidates
    
    def _score_thought(self, thought: str, context: Dict[str, Any]) -> float:
        """Score a thought (heuristic)."""
        # Simple heuristic scoring
        score = 0.5
        
        # Bonus for longer thoughts (more detail)
        if len(thought) > 50:
            score += 0.2
        
        # Bonus for specific keywords
        keywords = ["analysis", "approach", "solution", "design"]
        if any(kw in thought.lower() for kw in keywords):
            score += 0.1
        
        return min(score, 1.0)
    
    def _find_best_path(self, root_node: ThoughtNode) -> List[str]:
        """Find best path through the tree using backtracking."""
        best_path = []
        best_score = 0.0
        
        def dfs(node: ThoughtNode, current_path: List[str], current_score: float):
            nonlocal best_path, best_score
            
            current_path.append(node.id)
            current_score += node.score
            
            if not node.children_ids:
                # Leaf node - check if this is the best path
                if current_score > best_score:
                    best_score = current_score
                    best_path = current_path.copy()
            else:
                # Continue exploring children
                for child_id in node.children_ids:
                    if child_id in self._nodes:
                        dfs(self._nodes[child_id], current_path, current_score)
            
            current_path.pop()
        
        dfs(root_node, [], 0.0)
        return best_path
    
    def get_token_efficiency_score(self) -> float:
        """
        Calculate token efficiency score for ToT pattern.
        
        ToT is less efficient due to exploring multiple paths,
        but provides better quality through breadth-first exploration.
        """
        if not self._nodes:
            return 1.0
        
        # Efficiency decreases with more nodes
        base_efficiency = 0.6
        node_penalty = min(len(self._nodes) * 0.01, 0.3)
        return max(base_efficiency - node_penalty, 0.4)
