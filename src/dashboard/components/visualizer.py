from typing import Dict, List, Any, Optional

class Visualizer:
    """
    Paperclip-Grade Architectural Visualizer.
    Generates highly styled Mermaid diagrams for modern UI integration.
    """
    
    @staticmethod
    def generate_mermaid(thoughts_dict: Dict[str, Any]) -> str:
        """Converts thought archive into a beautifully styled Mermaid string."""
        if not thoughts_dict:
            return "graph TD\n    A[No cognitive data in this session]:::standard"

        # Theme Configuration (Paperclip Neutral)
        mermaid = [
            "%%{init: {\"theme\": \"base\", \"themeVariables\": {\"fontFamily\": \"Spline Sans, ui-sans-serif, system-ui\", \"primaryColor\": \"#FBF7EF\", \"primaryTextColor\": \"#0B1220\", \"primaryBorderColor\": \"rgba(15,23,42,0.16)\", \"lineColor\": \"rgba(15,23,42,0.22)\", \"tertiaryColor\": \"#F4EEDF\"}, \"flowchart\": {\"curve\": \"basis\"}}}%%",
            "graph TD",
            "    %% Component Styles",
            "    classDef standard fill:#FBF7EF,stroke:rgba(15,23,42,0.16),stroke-width:1px,color:#5B6472,font-weight:600,font-size:11px;",
            "    classDef hybrid fill:#EEF5FF,stroke:rgba(31,75,153,0.28),stroke-width:2px,color:#1F4B99,font-weight:800,font-size:11px;",
            "    classDef critical fill:#FFF1F2,stroke:rgba(190,18,60,0.22),stroke-width:2px,color:#9F1239,font-weight:800,font-size:11px;",
            "    classDef synthesis fill:#F0FDF4,stroke:rgba(22,163,74,0.22),stroke-width:2px,color:#166534,font-weight:800,font-size:11px;",
            "    classDef golden fill:#FFF7ED,stroke:rgba(180,83,9,0.30),stroke-width:2px,color:#B45309,font-weight:900,font-size:11px,stroke-dasharray: 4 4;"
        ]

        HYBRID_STRATEGIES = {
            "actor_critic_loop", "unconventional_pivot",
            "long_term_horizon", "multi_agent_fusion", "council_of_critics"
        }

        # Add Nodes
        for t_id, thought in thoughts_dict.items():
            strategy = thought.get("strategy", "").lower()
            t_type = thought.get("thought_type", "analysis").upper()
            short_id = t_id[-8:]
            is_golden = thought.get("is_thinking_pattern", False)
            
            # Select visual theme
            if is_golden:
                css = "golden"
            elif strategy in HYBRID_STRATEGIES:
                css = "hybrid"
            elif "critical" in strategy or "actor_critic" in strategy:
                css = "critical"
            elif strategy in ("synthesis", "integrative", "multi_agent_fusion"):
                css = "synthesis"
            else:
                css = "standard"

            # Clean labels for Mermaid
            safe_strat = strategy.upper()[:16].replace('_', ' ')
            label = f"{safe_strat}<br/>{t_type}<br/>{short_id}"
            
            mermaid.append(f'    n{t_id}["{label}"]:::{css}')

        # Add Edges
        for t_id, thought in thoughts_dict.items():
            parent_id = thought.get("parent_id")
            if parent_id and parent_id in thoughts_dict:
                mermaid.append(f"    n{parent_id} --> n{t_id}")

            for target in thought.get("builds_on", []):
                if target in thoughts_dict and target != parent_id:
                    mermaid.append(f"    n{t_id} -.-> n{target}")

            for target in thought.get("contradicts", []):
                if target in thoughts_dict:
                    mermaid.append(f"    n{t_id} --x n{target}")

        return "\n".join(mermaid)
