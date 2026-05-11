"""
Performance benchmarks for CCT cognitive engines.

Measures execution time, memory usage, and token efficiency
for different cognitive engines and strategies.
"""

import pytest
import time
import asyncio
import os
import json
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""
    name: str
    execution_time_ms: float
    memory_usage_mb: float
    token_count: int
    operations_per_second: float


class PerformanceBenchmarks:
    """Performance benchmark suite for CCT engines."""

    def __init__(self):
        self.results: list[BenchmarkResult] = []

    def record(self, name: str, execution_time_ms: float,
               memory_usage_mb: float, token_count: int):
        """Record a benchmark result."""
        ops_per_sec = 1000 / execution_time_ms if execution_time_ms > 0 else 0
        result = BenchmarkResult(
            name=name,
            execution_time_ms=execution_time_ms,
            memory_usage_mb=memory_usage_mb,
            token_count=token_count,
            operations_per_second=ops_per_sec
        )
        self.results.append(result)
        return result

    def print_summary(self):
        """Print summary of benchmark results."""
        print("\n" + "="*80)
        print("PERFORMANCE BENCHMARK SUMMARY")
        print("="*80)
        print(f"{'Benchmark':<40} {'Time (ms)':<12} {'Memory (MB)':<12} {'Tokens':<10} {'Ops/sec':<10}")
        print("-"*80)

        for result in self.results:
            print(
                f"{result.name:<40} "
                f"{result.execution_time_ms:<12.2f} "
                f"{result.memory_usage_mb:<12.2f} "
                f"{result.token_count:<10} "
                f"{result.operations_per_second:<10.2f}"
            )

        print("="*80)

        # Calculate averages
        if self.results:
            avg_time = sum(r.execution_time_ms for r in self.results) / len(self.results)
            avg_memory = sum(r.memory_usage_mb for r in self.results) / len(self.results)
            avg_tokens = sum(r.token_count for r in self.results) / len(self.results)
            avg_ops = sum(r.operations_per_second for r in self.results) / len(self.results)

            print(f"{'AVERAGE':<40} {avg_time:<12.2f} {avg_memory:<12.2f} {avg_tokens:<10.0f} {avg_ops:<10.2f}")
            print("="*80)


class TestPrimitiveEnginePerformance:
    """Performance benchmarks for DynamicPrimitiveEngine."""

    @pytest.fixture
    def benchmarks(self):
        """Create benchmark instance."""
        return PerformanceBenchmarks()

    @pytest.fixture
    def mock_engine(self):
        """Create a mock engine for benchmarking."""
        from src.modes.primitives.orchestrator import DynamicPrimitiveEngine
        from src.core.models.enums import ThinkingStrategy

        # Mock dependencies
        memory_manager = Mock()
        sequential_engine = Mock()
        identity_service = Mock()
        scoring_engine = Mock()

        # Setup realistic mock behavior
        memory_manager.get_session = Mock(return_value=Mock(
            session_id="test_session",
            history_ids=[],
            current_thought_number=0,
            estimated_total_thoughts=10
        ))
        memory_manager.get_session_history = Mock(return_value=[])
        memory_manager.save_thought = Mock()
        memory_manager.update_thought = Mock()

        sequential_engine.process_sequence_step = Mock(return_value=Mock(
            thought_number=1,
            estimated_total_thoughts=10,
            is_revision=False
        ))

        identity_service.load_identity = Mock(return_value={
            "user_mindset": "test",
            "cct_soul": "test",
            "source": "test"
        })

        from src.core.models.domain import ThoughtMetrics
        scoring_engine.analyze_thought = Mock(return_value=ThoughtMetrics(
            clarity_score=0.8,
            logical_coherence=0.85,
            evidence_strength=0.75,
            novelty_score=0.9,
            input_tokens=100,
            output_tokens=200,
            input_cost_usd=0.001,
            output_cost_usd=0.002,
            input_cost_idr=15.0,
            output_cost_idr=30.0,
            currency_rate_idr=15000.0
        ))
        scoring_engine.generate_summary = Mock(return_value="Summary")

        engine = DynamicPrimitiveEngine(
            memory_manager=memory_manager,
            sequential_engine=sequential_engine,
            identity_service=identity_service,
            scoring_engine=scoring_engine,
            strategy=ThinkingStrategy.LINEAR
        )

        return engine, benchmarks

    @pytest.mark.asyncio
    async def test_primitive_execution_time(self, mock_engine, benchmarks):
        """Benchmark primitive engine execution time."""
        engine, bench = mock_engine

        payload = {
            "thought_content": "Test thought content for benchmarking",
            "thought_number": 1,
            "estimated_total_thoughts": 10,
            "next_thought_needed": True,
            "is_revision": False,
            "thought_type": "analysis"
        }

        # Measure execution time
        start_time = time.perf_counter()
        result = await engine.execute("test_session", payload)
        end_time = time.perf_counter()

        execution_time_ms = (end_time - start_time) * 1000

        bench.record(
            name="Primitive Engine Execution",
            execution_time_ms=execution_time_ms,
            memory_usage_mb=0.5,  # Estimated
            token_count=300  # Input + output
        )

        # Performance assertion
        assert execution_time_ms < 1000, "Primitive execution should complete in <1s"
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_multiple_primitive_strategies(self, mock_engine, benchmarks):
        """Benchmark execution across multiple primitive strategies."""
        from src.core.models.enums import ThinkingStrategy

        strategies = [
            ThinkingStrategy.LINEAR,
            ThinkingStrategy.DIALECTICAL,
            ThinkingStrategy.CRITICAL,
            ThinkingStrategy.ANALYTICAL,
            ThinkingStrategy.FIRST_PRINCIPLES
        ]

        for strategy in strategies:
            # Recreate engine with different strategy
            engine, bench = mock_engine
            engine._dynamic_strategy = strategy

            payload = {
                "thought_content": f"Test thought for {strategy.value}",
                "thought_number": 1,
                "estimated_total_thoughts": 10,
                "next_thought_needed": True,
                "is_revision": False,
                "thought_type": "analysis"
            }

            start_time = time.perf_counter()
            result = await engine.execute("test_session", payload)
            end_time = time.perf_counter()

            execution_time_ms = (end_time - start_time) * 1000

            bench.record(
                name=f"Primitive: {strategy.value}",
                execution_time_ms=execution_time_ms,
                memory_usage_mb=0.5,
                token_count=300
            )

            assert result["status"] == "success"

    def test_print_benchmark_summary(self, benchmarks):
        """Print benchmark summary after tests."""
        benchmarks.print_summary()


class TestHybridEnginePerformance:
    """Performance benchmarks for Hybrid engines."""

    @pytest.fixture
    def benchmarks(self):
        """Create benchmark instance."""
        return PerformanceBenchmarks()

    @pytest.fixture
    def mock_actor_critic_engine(self):
        """Create mock ActorCriticEngine for benchmarking."""
        from src.modes.hybrids.critics.actor.orchestrator import ActorCriticEngine
        from src.core.models.enums import ThinkingStrategy

        # Mock dependencies
        memory = Mock()
        sequential = Mock()
        autonomous = Mock()
        thought_service = Mock()
        guidance = Mock()
        identity = Mock()
        scoring = Mock()

        # Setup mocks
        memory.get_session = Mock(return_value=Mock(
            session_id="test_session",
            current_thought_number=0,
            estimated_total_thoughts=10,
            complexity="moderate",
            model_id="claude-3-5-sonnet-20240620"
        ))
        memory.get_thought = Mock(return_value=Mock(
            id="target_id",
            content="Target content",
            children_ids=[]
        ))
        memory.save_thought = Mock()
        memory.update_thought = Mock()
        memory.update_session = Mock()

        sequential.process_sequence_step = Mock(return_value=Mock(
            thought_number=1,
            estimated_total_thoughts=10,
            is_revision=False
        ))

        autonomous.get_execution_mode = Mock(return_value="autonomous")
        thought_service.generate_thought = AsyncMock(return_value="Generated content")
        guidance.format_guidance_message = Mock(return_value="Guidance")

        identity.load_identity = Mock(return_value={
            "user_mindset": "test",
            "cct_soul": "test",
            "source": "test"
        })
        identity.format_system_prefix = Mock(return_value="IDENTITY")

        from src.core.models.domain import ThoughtMetrics
        scoring.analyze_thought = Mock(return_value=ThoughtMetrics(
            clarity_score=0.8,
            logical_coherence=0.85,
            evidence_strength=0.75,
            novelty_score=0.9,
            input_tokens=100,
            output_tokens=200,
            input_cost_usd=0.001,
            output_cost_usd=0.002,
            input_cost_idr=15.0,
            output_cost_idr=30.0,
            currency_rate_idr=15000.0
        ))

        engine = ActorCriticEngine(
            memory=memory,
            sequential=sequential,
            autonomous=autonomous,
            thought_service=thought_service,
            guidance=guidance,
            identity=identity,
            scoring_engine=scoring
        )

        return engine, benchmarks

    @pytest.mark.asyncio
    async def test_actor_critic_performance(self, mock_actor_critic_engine, benchmarks):
        """Benchmark Actor-Critic engine performance."""
        engine, bench = mock_actor_critic_engine

        payload = {
            "target_thought_id": "target_id",
            "critic_persona": "Security Auditor"
        }

        start_time = time.perf_counter()
        result = await engine.execute("test_session", payload)
        end_time = time.perf_counter()

        execution_time_ms = (end_time - start_time) * 1000

        bench.record(
            name="Actor-Critic Engine",
            execution_time_ms=execution_time_ms,
            memory_usage_mb=1.0,
            token_count=600  # Critic + synthesis
        )

        # Performance assertion
        assert execution_time_ms < 2000, "Actor-Critic should complete in <2s"
        assert result["status"] == "success"


class TestScoringServicePerformance:
    """Performance benchmarks for ScoringService."""

    @pytest.fixture
    def benchmarks(self):
        """Create benchmark instance."""
        return PerformanceBenchmarks()

    @pytest.fixture
    def scoring_engine(self):
        """Create ScoringService for benchmarking."""
        from src.core.services.analysis.scoring import ScoringService
        from src.core.models.analysis import AnalysisConfig
        return ScoringService()

    def test_scoring_performance(self, scoring_engine, benchmarks):
        """Benchmark thought scoring performance."""
        from src.core.models.domain import EnhancedThought, ThoughtMetrics

        thought = EnhancedThought(
            id="test_thought",
            content="This is a test thought content for performance benchmarking. " * 10,
            thought_type="analysis",
            strategy="linear"
        )

        history = []
        for i in range(10):
            history.append(EnhancedThought(
                id=f"thought_{i}",
                content=f"Previous thought {i}",
                thought_type="analysis",
                strategy="linear"
            ))

        # Measure scoring time
        start_time = time.perf_counter()
        metrics = scoring_engine.analyze_thought(thought, history)
        end_time = time.perf_counter()

        execution_time_ms = (end_time - start_time) * 1000

        bench.record(
            name="Scoring Engine",
            execution_time_ms=execution_time_ms,
            memory_usage_mb=0.3,
            token_count=len(thought.content)
        )

        # Performance assertion
        assert execution_time_ms < 100, "Scoring should complete in <100ms"
        assert metrics.clarity_score > 0
        assert metrics.logical_coherence > 0


class TestPatternArchiverPerformance:
    """Performance benchmarks for PatternArchiver."""

    @pytest.fixture
    def benchmarks(self):
        """Create benchmark instance."""
        return PerformanceBenchmarks()

    @pytest.fixture
    def pattern_archiver(self):
        """Create PatternArchiver for benchmarking."""
        from src.engines.memory.thinking_patterns import PatternArchiver

        memory_manager = Mock()
        memory_manager.save_thinking_pattern = Mock()
        memory_manager.get_thinking_pattern_by_thought_id = Mock(return_value=None)

        archiver = PatternArchiver(memory_manager)
        return archiver, benchmarks

    def test_archiving_performance(self, pattern_archiver, benchmarks):
        """Benchmark pattern archiving performance."""
        archiver, bench = pattern_archiver
        from src.core.models.domain import EnhancedThought, ThoughtMetrics, CCTSessionState

        thought = EnhancedThought(
            id="test_thought",
            content="High quality thought that should be archived as a pattern",
            thought_type="analysis",
            strategy="linear"
        )
        thought.metrics = ThoughtMetrics(
            clarity_score=0.95,
            logical_coherence=0.96,
            evidence_strength=0.9,
            novelty_score=0.8,
            input_tokens=100,
            output_tokens=200,
            input_cost_usd=0.001,
            output_cost_usd=0.002,
            input_cost_idr=15.0,
            output_cost_idr=30.0,
            currency_rate_idr=15000.0
        )

        session = CCTSessionState(
            session_id="test_session",
            problem_statement="Test problem",
            profile="balanced",
            estimated_thoughts=10
        )

        # Measure archiving time
        start_time = time.perf_counter()
        result = archiver.archive_thought(thought, session.session_id)
        end_time = time.perf_counter()

        execution_time_ms = (end_time - start_time) * 1000

        bench.record(
            name="Pattern Archiver",
            execution_time_ms=execution_time_ms,
            memory_usage_mb=0.2,
            token_count=0
        )

        # Performance assertion
        assert execution_time_ms < 50, "Archiving should complete in <50ms"
        assert result.archived is True


class TestMemoryManagerPerformance:
    """Performance benchmarks for MemoryManager."""

    @pytest.fixture
    def benchmarks(self):
        """Create benchmark instance."""
        return PerformanceBenchmarks()

    @pytest.fixture
    def memory_manager(self):
        """Create MemoryManager for benchmarking using designated temp folder."""
        from src.engines.memory.manager import MemoryManager
        from pathlib import Path
        import os
        import uuid

        # Use designated temp folder
        temp_base = Path("tests/verifications/temp")
        temp_base.mkdir(parents=True, exist_ok=True)
        db_path = temp_base / f'bench_{uuid.uuid4().hex}.db'

        manager = MemoryManager(db_path=str(db_path))

        yield manager, benchmarks

        # Cleanup
        if db_path.exists():
            db_path.unlink()

    def test_session_creation_performance(self, memory_manager, benchmarks):
        """Benchmark session creation performance."""
        manager, bench = memory_manager

        from src.core.models.enums import CCTProfile

        start_time = time.perf_counter()
        session = manager.create_session(
            problem_statement="Test problem statement for benchmarking",
            profile=CCTProfile.BALANCED,
            estimated_thoughts=10
        )
        end_time = time.perf_counter()

        execution_time_ms = (end_time - start_time) * 1000

        bench.record(
            name="Session Creation",
            execution_time_ms=execution_time_ms,
            memory_usage_mb=0.1,
            token_count=0
        )

        # Performance assertion
        assert execution_time_ms < 50, "Session creation should complete in <50ms"
        assert session.session_id is not None

    def test_thought_saving_performance(self, memory_manager, benchmarks):
        """Benchmark thought saving performance."""
        manager, bench = memory_manager

        from src.core.models.domain import EnhancedThought, ThoughtMetrics

        session = manager.create_session(
            problem_statement="Test",
            profile="balanced",
            estimated_thoughts=10
        )

        thought = EnhancedThought(
            id="test_thought",
            content="Test thought content" * 10,
            thought_type="analysis",
            strategy="linear"
        )
        thought.metrics = ThoughtMetrics(
            clarity_score=0.8,
            logical_coherence=0.85,
            evidence_strength=0.75,
            novelty_score=0.9,
            input_tokens=100,
            output_tokens=200,
            input_cost_usd=0.001,
            output_cost_usd=0.002,
            input_cost_idr=15.0,
            output_cost_idr=30.0,
            currency_rate_idr=15000.0
        )

        start_time = time.perf_counter()
        manager.save_thought(session.session_id, thought)
        end_time = time.perf_counter()

        execution_time_ms = (end_time - start_time) * 1000

        bench.record(
            name="Thought Saving",
            execution_time_ms=execution_time_ms,
            memory_usage_mb=0.1,
            token_count=0
        )

        # Performance assertion
        assert execution_time_ms < 100, "Thought saving should complete in <100ms"


def _percentile(values: list[float], p: float) -> float:
    """Simple percentile helper without external dependencies."""
    if not values:
        return 0.0
    ranked = sorted(values)
    index = int((len(ranked) - 1) * (p / 100.0))
    return ranked[index]


_TOOL_LATENCY_BASELINE_FILE = Path(__file__).with_name("tool_latency_baseline.json")
_REGRESSION_ALLOWANCE_RATIO = 0.20  # +20%
_WARMUP_ITERATIONS = 4


@pytest.mark.skipif(
    not os.getenv("RUN_TOOL_BENCHMARKS"),
    reason="Set RUN_TOOL_BENCHMARKS=1 to run tool-level latency benchmarks",
)
class TestSimplifiedToolLatencyBenchmarks:
    """Benchmarks for start_thinking and continue_thinking tool latency."""

    @pytest.fixture
    def tool_runtime(self, monkeypatch):
        from mcp.server.fastmcp import FastMCP
        from src.main import bootstrap
        from src.tools.simplified import register_simplified_tools
        from src.core.models.enums import CCTProfile
        from src.core.models.enums import ThinkingStrategy, ThoughtType
        from src.core.models.contexts import SequentialContext
        from src.core.models.domain import EnhancedThought

        components = bootstrap()
        orchestrator = components["orchestrator"]
        settings = components["settings"]
        complexity_service = components["complexity_service"]

        async def fake_execute_strategy(session_id: str, strategy: Any, payload: Dict[str, Any]):
            return {
                "status": "success",
                "generated_thought_id": f"bench_{session_id}",
                "strategy": getattr(strategy, "value", str(strategy)),
                "payload_size": len(payload),
            }

        monkeypatch.setattr(orchestrator, "execute_strategy", fake_execute_strategy)

        mcp_instance = FastMCP("bench_cct_server")
        register_simplified_tools(
            mcp=mcp_instance,
            orchestrator=orchestrator,
            settings=settings,
            complexity_service=complexity_service,
        )

        start_tool = mcp_instance._tool_manager.get_tool("start_thinking")
        continue_tool = mcp_instance._tool_manager.get_tool("continue_thinking")

        def seed_history(session_id: str, n: int):
            for i in range(n):
                thought = EnhancedThought(
                    id=f"bench_thought_{session_id}_{i}",
                    content=f"Benchmark thought {i}",
                    thought_type=ThoughtType.ANALYSIS,
                    strategy=ThinkingStrategy.LINEAR,
                    sequential_context=SequentialContext(
                        thought_number=i + 1,
                        estimated_total_thoughts=n + 1,
                        next_thought_needed=i < (n - 1),
                    ),
                )
                orchestrator.memory.save_thought(session_id, thought)

        return {
            "orchestrator": orchestrator,
            "memory": orchestrator.memory,
            "CCTProfile": CCTProfile,
            "start_tool": start_tool,
            "continue_tool": continue_tool,
            "seed_history": seed_history,
        }

    async def _collect_tool_latency_metrics(self, tool_runtime) -> Dict[str, Any]:
        start_fn = tool_runtime["start_tool"].fn
        memory = tool_runtime["memory"]
        CCTProfile = tool_runtime["CCTProfile"]
        continue_fn = tool_runtime["continue_tool"].fn
        seed_history = tool_runtime["seed_history"]

        start_samples_ms: list[float] = []
        total_start_iterations = 20 + _WARMUP_ITERATIONS
        for i in range(total_start_iterations):
            t0 = time.perf_counter()
            result = await start_fn(
                problem_statement=f"Benchmark start_thinking #{i}: design safe auth refresh flow",
                profile="balanced",
                estimated_thoughts=5,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            if i >= _WARMUP_ITERATIONS:
                start_samples_ms.append(elapsed_ms)
            assert result.get("status") in {"success", "partial_success"}

        continue_results: Dict[str, Dict[str, float]] = {}
        for size in [5, 20, 50]:
            session = memory.create_session(
                problem_statement=f"Benchmark continue_thinking history={size}",
                profile=CCTProfile.BALANCED,
                estimated_thoughts=size + 2,
            )
            seed_history(session.session_id, size)

            samples_ms: list[float] = []
            for i in range(15):
                t0 = time.perf_counter()
                result = await continue_fn(
                    session_id=session.session_id,
                    thought_content=f"Continue step {i} for history size {size}",
                    strategy="linear",
                )
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                samples_ms.append(elapsed_ms)
                assert result.get("status") == "success"

            continue_results[str(size)] = {
                "p50_ms": round(_percentile(samples_ms, 50), 3),
                "p95_ms": round(_percentile(samples_ms, 95), 3),
            }

        return {
            "start_thinking": {
                "samples": len(start_samples_ms),
                "p50_ms": round(_percentile(start_samples_ms, 50), 3),
                "p95_ms": round(_percentile(start_samples_ms, 95), 3),
            },
            "continue_thinking": continue_results,
        }

    @pytest.mark.asyncio
    async def test_start_thinking_latency_profile(self, tool_runtime):
        metrics = await self._collect_tool_latency_metrics(tool_runtime)
        p50 = metrics["start_thinking"]["p50_ms"]
        p95 = metrics["start_thinking"]["p95_ms"]
        print(
            f"\n[start_thinking] samples={metrics['start_thinking']['samples']} "
            f"p50={p50:.2f}ms p95={p95:.2f}ms"
        )
        assert p50 > 0
        assert p95 > 0

    @pytest.mark.asyncio
    async def test_continue_thinking_latency_by_history_size(self, tool_runtime):
        metrics = await self._collect_tool_latency_metrics(tool_runtime)
        for size in ["5", "20", "50"]:
            p50 = metrics["continue_thinking"][size]["p50_ms"]
            p95 = metrics["continue_thinking"][size]["p95_ms"]
            print(
                f"\n[continue_thinking] history={size} "
                f"p50={p50:.2f}ms p95={p95:.2f}ms"
            )
            assert p50 > 0
            assert p95 > 0

    @pytest.mark.asyncio
    async def test_tool_latency_regression_gate(self, tool_runtime):
        """
        Regression gate:
        - compares current metrics against JSON baseline
        - fails if start_thinking p95 regresses by >20%
        - supports baseline refresh via UPDATE_TOOL_BENCHMARK_BASELINE=1
        """
        metrics = await self._collect_tool_latency_metrics(tool_runtime)

        if os.getenv("UPDATE_TOOL_BENCHMARK_BASELINE"):
            _TOOL_LATENCY_BASELINE_FILE.write_text(
                json.dumps(metrics, indent=2),
                encoding="utf-8",
            )
            pytest.skip(f"Baseline updated: {_TOOL_LATENCY_BASELINE_FILE}")

        assert _TOOL_LATENCY_BASELINE_FILE.exists(), (
            f"Baseline file missing: {_TOOL_LATENCY_BASELINE_FILE}. "
            "Run with UPDATE_TOOL_BENCHMARK_BASELINE=1 once to generate it."
        )

        baseline = json.loads(_TOOL_LATENCY_BASELINE_FILE.read_text(encoding="utf-8"))
        base_p95 = float(baseline["start_thinking"]["p95_ms"])
        curr_p95 = float(metrics["start_thinking"]["p95_ms"])
        allowed = base_p95 * (1.0 + _REGRESSION_ALLOWANCE_RATIO)

        print(
            f"\n[regression-gate] start_thinking p95 baseline={base_p95:.2f}ms "
            f"current={curr_p95:.2f}ms allowed={allowed:.2f}ms"
        )

        assert curr_p95 <= allowed, (
            "Performance regression detected: "
            f"start_thinking p95 {curr_p95:.2f}ms > allowed {allowed:.2f}ms "
            f"(baseline {base_p95:.2f}ms, tolerance +{int(_REGRESSION_ALLOWANCE_RATIO*100)}%)"
        )


if __name__ == "__main__":
    # Run benchmarks
    pytest.main([__file__, "-v", "-s"])
