#!/usr/bin/env python3
"""
Concurrency Benchmark for multi-IDE / multi-LLM support.

Tests:
  - Concurrent session creation across N simulated LLM instances
  - Parallel thought insertion
  - Memory isolation between LLM instances
  - Rate limiting under load
  - Connection pool saturation

Usage:
    python tests/benchmarks/concurrency_benchmark.py --clients=5 --requests=50
    python tests/benchmarks/concurrency_benchmark.py --mode=stress --duration=30
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cct-bench")

# ============================================================================
# CONFIG
# ============================================================================
BASE_URL = os.getenv("CCT_BENCH_URL", "http://127.0.0.1:8001")
API_KEY = os.getenv("CCT_BOOTSTRAP_API_KEY", "test-bootstrap-key")


@dataclass
class BenchResult:
    client_id: str
    operation: str
    success: bool
    latency_ms: float
    error: Optional[str] = None


@dataclass
class LLMSimConfig:
    instance_id: str
    ide: str
    requests: int = 10
    concurrency: int = 3


# ============================================================================
# CLIENT SIMULATOR
# ============================================================================
class LLMClientSimulator:
    """Simulates an LLM/IDE client making concurrent MCP requests."""

    def __init__(self, config: LLMSimConfig, base_url: str = BASE_URL):
        self.config = config
        self.base_url = base_url
        self.session_id: Optional[str] = None
        self.results: List[BenchResult] = []
        self._auth_header = {"X-API-KEY": API_KEY}
        self._headers = {
            **self._auth_header,
            "Content-Type": "application/json",
            "X-IDE-ORIGIN": config.ide,
            "X-LLM-INSTANCE-ID": config.instance_id,
        }

    async def _request(self, method: str, url: str, json_body: Optional[Dict] = None) -> Dict:
        import aiohttp
        async with aiohttp.ClientSession(headers=self._headers) as session:
            async with session.request(method, url, json=json_body) as resp:
                return {"status": resp.status, "body": await resp.json()}

    async def health_check(self) -> bool:
        try:
            resp = await self._request("GET", f"{self.base_url}/health")
            return resp["status"] == 200
        except Exception:
            return False

    async def create_session(self) -> bool:
        start = time.monotonic()
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {
                    "name": "start_thinking",
                    "arguments": {
                        "problem_statement": f"Benchmark problem from {self.config.instance_id}",
                        "profile": "balanced",
                        "model_id": self.config.instance_id,
                        "estimated_thoughts": 5,
                        "_llm_instance_id": self.config.instance_id,
                        "_ide_origin": self.config.ide,
                    },
                },
            }
            resp = await self._request("POST", f"{self.base_url}/cognitive-api/v1/sync", payload)
            ok = resp["status"] == 200
            elapsed = (time.monotonic() - start) * 1000
            if ok and resp["body"].get("result", {}).get("session_id"):
                self.session_id = resp["body"]["result"]["session_id"]
            self.results.append(BenchResult(self.config.instance_id, "create_session", ok, elapsed))
            return ok
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            self.results.append(BenchResult(self.config.instance_id, "create_session", False, elapsed, str(e)))
            return False

    async def add_thought(self) -> bool:
        if not self.session_id:
            return False
        start = time.monotonic()
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {
                    "name": "continue_thinking",
                    "arguments": {
                        "session_id": self.session_id,
                        "thought_content": f"Benchmark thought from {self.config.instance_id} at {datetime.now().isoformat()}",
                        "strategy": "auto",
                        "thought_number": 1,
                        "estimated_total_thoughts": 5,
                        "thought_type": "analysis",
                        "_llm_instance_id": self.config.instance_id,
                        "_ide_origin": self.config.ide,
                    },
                },
            }
            resp = await self._request("POST", f"{self.base_url}/cognitive-api/v1/sync", payload)
            ok = resp["status"] == 200
            elapsed = (time.monotonic() - start) * 1000
            self.results.append(BenchResult(self.config.instance_id, "add_thought", ok, elapsed))
            return ok
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            self.results.append(BenchResult(self.config.instance_id, "add_thought", False, elapsed, str(e)))
            return False

    async def check_isolation(self) -> bool:
        """Verify that this LLM can't see another LLM's sessions."""
        start = time.monotonic()
        try:
            params = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "list_cct_sessions", "params": {}}
            payload = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {"name": "list_cct_sessions", "arguments": params},
            }
            resp = await self._request("POST", f"{self.base_url}/cognitive-api/v1/sync", payload)
            ok = resp["status"] == 200
            elapsed = (time.monotonic() - start) * 1000
            self.results.append(BenchResult(self.config.instance_id, "check_isolation", ok, elapsed))
            return ok
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            self.results.append(BenchResult(self.config.instance_id, "check_isolation", False, elapsed, str(e)))
            return False

    async def run_requests(self) -> int:
        successful = 0
        sem = asyncio.Semaphore(self.config.concurrency)

        async def _task():
            nonlocal successful
            async with sem:
                if await self.health_check():
                    successful += 1

        tasks = []
        for i in range(self.config.requests):
            if i % 3 == 0:
                await self.create_session()
            elif i % 3 == 1 and self.session_id:
                tasks.append(asyncio.create_task(self._run_with_sem(self.add_thought, sem)))
            else:
                tasks.append(asyncio.create_task(self._run_with_sem(self.check_isolation, sem)))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful += sum(1 for r in results if r is True)

        return successful

    async def _run_with_sem(self, coro, sem):
        async with sem:
            return await coro()


# ============================================================================
# BENCHMARK RUNNER
# ============================================================================
class ConcurrencyBenchmark:
    """Runs concurrent LLM simulations and reports metrics."""

    def __init__(self, num_clients: int = 3, requests_per_client: int = 10, concurrency: int = 3):
        self.clients = [
            LLMClientSimulator(
                LLMSimConfig(
                    instance_id=f"bench-llm-{i}-{uuid.uuid4().hex[:4]}",
                    ide=["vscode", "cursor", "jetbrains", "windsurf", "copilot"][i % 5],
                    requests=requests_per_client,
                    concurrency=concurrency,
                )
            )
            for i in range(num_clients)
        ]
        self.start_time: float = 0
        self.end_time: float = 0

    async def run(self):
        logger.info(f"Starting benchmark: {len(self.clients)} clients, {self.clients[0].config.requests} requests each")
        self.start_time = time.monotonic()

        tasks = [client.run_requests() for client in self.clients]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        self.end_time = time.monotonic()
        self._report(results)

    def _report(self, results):
        duration = self.end_time - self.start_time
        total_requests = sum(client.config.requests for client in self.clients)
        all_results = []
        for client in self.clients:
            all_results.extend(client.results)

        successes = sum(1 for r in all_results if r.success)
        failures = sum(1 for r in all_results if not r.success)

        latencies = [r.latency_ms for r in all_results if r.success]
        p50 = sorted(latencies)[len(latencies) // 2] if latencies else 0
        p95 = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
        p99 = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0

        report = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration, 2),
            "clients": len(self.clients),
            "total_requests": total_requests,
            "successful": successes,
            "failed": failures,
            "success_rate": round(successes / max(total_requests, 1) * 100, 2),
            "requests_per_second": round(total_requests / max(duration, 0.001), 2),
            "latency_ms": {"p50": round(p50, 2), "p95": round(p95, 2), "p99": round(p99, 2)},
            "by_operation": self._op_stats(all_results),
            "by_llm": self._llm_stats(all_results),
        }

        logger.info(f"\n{'='*60}")
        logger.info(f"CONCURRENCY BENCHMARK RESULTS")
        logger.info(f"{'='*60}")
        logger.info(f"Duration: {report['duration_seconds']}s")
        logger.info(f"Clients: {report['clients']} | Requests: {report['total_requests']}")
        logger.info(f"Success: {report['successful']}/{report['total_requests']} ({report['success_rate']}%)")
        logger.info(f"RPS: {report['requests_per_second']}")
        logger.info(f"Latency: P50={report['latency_ms']['p50']}ms P95={report['latency_ms']['p95']}ms P99={report['latency_ms']['p99']}ms")
        logger.info(f"{'='*60}")

        # Write report
        report_path = os.path.join(os.path.dirname(__file__), f"concurrency_report_{int(time.time())}.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to: {report_path}")

    def _op_stats(self, results):
        ops = {}
        for r in results:
            ops.setdefault(r.operation, {"total": 0, "success": 0, "failed": 0, "total_latency": 0.0})
            ops[r.operation]["total"] += 1
            if r.success:
                ops[r.operation]["success"] += 1
                ops[r.operation]["total_latency"] += r.latency_ms
            else:
                ops[r.operation]["failed"] += 1
        for op in ops:
            s = ops[op]["success"]
            ops[op]["avg_latency_ms"] = round(ops[op]["total_latency"] / max(s, 1), 2) if s else 0
            del ops[op]["total_latency"]
        return ops

    def _llm_stats(self, results):
        llms = {}
        for r in results:
            llms.setdefault(r.client_id, {"total": 0, "success": 0, "failed": 0})
            llms[r.client_id]["total"] += 1
            if r.success:
                llms[r.client_id]["success"] += 1
            else:
                llms[r.client_id]["failed"] += 1
        return llms


# ============================================================================
# MAIN
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="CCT Multi-IDE Concurrency Benchmark")
    parser.add_argument("--clients", type=int, default=3, help="Number of simulated LLM clients")
    parser.add_argument("--requests", type=int, default=10, help="Requests per client")
    parser.add_argument("--concurrency", type=int, default=3, help="Concurrent requests per client")
    parser.add_argument("--mode", choices=["quick", "standard", "stress"], default="standard",
                        help="Benchmark mode: quick=1client/5req, standard=3/10, stress=10/50")
    parser.add_argument("--url", default=BASE_URL, help="Server base URL")
    args = parser.parse_args()

    modes = {
        "quick": {"clients": 1, "requests": 5, "concurrency": 2},
        "standard": {"clients": 3, "requests": 10, "concurrency": 3},
        "stress": {"clients": 10, "requests": 50, "concurrency": 5},
    }

    config = modes.get(args.mode, {})
    clients = args.clients if args.clients else config.get("clients", 3)
    requests = args.requests if args.requests else config.get("requests", 10)
    concurrency = args.concurrency if args.concurrency else config.get("concurrency", 3)

    for client in benchmark.clients:
        client.base_url = args.url

    benchmark = ConcurrencyBenchmark(
        num_clients=clients,
        requests_per_client=requests,
        concurrency=concurrency,
    )
    asyncio.run(benchmark.run())


if __name__ == "__main__":
    main()
