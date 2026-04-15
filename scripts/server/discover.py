#!/usr/bin/env python
"""
CCT Server Discovery and Management CLI

Standalone tool for discovering, starting, and managing CCT servers
for multi-agent scenarios.

Author: Steeven Andrian — Senior Systems Architect

CLI Usage:
    python scripts/server/discover.py scan          # Scan for running servers
    python scripts/server/discover.py start         # Start server if not running
    python scripts/server/discover.py status        # Show detailed status
    python scripts/server/discover.py health        # Health check

Programmatic Usage:
    from scripts.server.discover import CCTServerDiscovery, CCTServerPool
    
    discovery = CCTServerDiscovery()
    servers = await discovery.scan()
"""
from __future__ import annotations

import asyncio
import httpx
import logging
import subprocess
import time
import socket
import sys
import os
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

VERSION = "1.0.0"

def show_banner():
    """Display the CCT banner with author info."""
    print(f"\n  CCT COGNITIVE SERVER {VERSION}")
    print("  Crafted By Steeven Andrian Salim - https://github.com/steevenz\n")


@dataclass
class ServerInstance:
    """Represents a discovered or managed CCT server instance."""
    host: str
    port: int
    url: str
    process: Optional[subprocess.Popen] = None
    is_managed: bool = False
    last_health_check: Optional[float] = None
    is_healthy: bool = False
    connection_count: int = 0
    started_at: Optional[float] = None
    uptime_seconds: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['uptime_seconds'] = self.get_uptime()
        return data
    
    def get_uptime(self) -> Optional[float]:
        """Get server uptime in seconds."""
        if self.started_at:
            return time.time() - self.started_at
        return None


class CCTServerDiscovery:
    """
    Discovers running CCT servers on the network or local machine.
    """
    
    DEFAULT_PORTS = [8000, 8001, 8002, 8080, 3000, 5000, 3001, 5001]
    DEFAULT_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]
    HEALTH_ENDPOINT = "/cognitive-api/v1/sync"
    TIMEOUT = 2.0
    
    def __init__(
        self,
        hosts: Optional[List[str]] = None,
        ports: Optional[List[int]] = None,
        timeout: float = 2.0
    ):
        self.hosts = hosts or self.DEFAULT_HOSTS
        self.ports = ports or self.DEFAULT_PORTS
        self.timeout = timeout
        self._discovered: Dict[str, ServerInstance] = {}
    
    async def scan(self, verbose: bool = False) -> List[ServerInstance]:
        """
        Scan for running CCT servers.
        Returns list of available server instances.
        """
        discovered = []
        
        tasks = []
        for host in self.hosts:
            for port in self.ports:
                tasks.append(self._check_server(host, port, verbose))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, ServerInstance):
                discovered.append(result)
                self._discovered[f"{result.host}:{result.port}"] = result
            elif isinstance(result, Exception) and verbose:
                logger.debug(f"Check failed: {result}")
        
        logger.info(f"[DISCOVERY] Found {len(discovered)} CCT server(s)")
        return discovered
    
    async def _check_server(self, host: str, port: int, verbose: bool = False) -> Optional[ServerInstance]:
        """Check if a CCT server is running at host:port."""
        url = f"http://{host}:{port}"
        health_url = f"{url}{self.HEALTH_ENDPOINT}"
        
        try:
            # Try HTTP health endpoint first
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(health_url)
                    if response.status_code in (200, 404, 405):
                        if verbose:
                            logger.info(f"  ✓ {host}:{port} - HTTP endpoint responding")
                        return ServerInstance(
                            host=host,
                            port=port,
                            url=url,
                            is_healthy=True,
                            last_health_check=time.time()
                        )
            except httpx.HTTPError:
                if verbose:
                    logger.debug(f"  - {host}:{port} - HTTP not responding")
            except Exception as e:
                if verbose:
                    logger.debug(f"  - {host}:{port} - HTTP error: {e}")
            
            # Fallback: TCP connection check
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    if verbose:
                        logger.info(f"  ✓ {host}:{port} - Port open (TCP)")
                    return ServerInstance(
                        host=host,
                        port=port,
                        url=url,
                        is_healthy=True,
                        last_health_check=time.time()
                    )
            except Exception as e:
                if verbose:
                    logger.debug(f"  - {host}:{port} - TCP error: {e}")
                    
        except Exception as e:
            if verbose:
                logger.debug(f"[DISCOVERY] Check failed for {host}:{port}: {e}")
        
        return None
    
    def get_local_server(self, port: int = 8001) -> str:
        """Get URL for local server at specific port."""
        return f"http://localhost:{port}"


class CCTServerPool:
    """
    Connection pool for multi-agent CCT server access.
    """
    
    def __init__(
        self,
        auto_start: bool = True,
        preferred_port: int = 8001,
        project_root: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        startup_timeout: int = 30
    ):
        self.auto_start = auto_start
        self.preferred_port = preferred_port
        self.project_root = project_root
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.startup_timeout = startup_timeout
        
        self.discovery = CCTServerDiscovery(
            ports=[preferred_port] + CCTServerDiscovery.DEFAULT_PORTS,
            timeout=1.0
        )
        self._server: Optional[ServerInstance] = None
        self._lock = asyncio.Lock()
        self._health_check_task: Optional[asyncio.Task] = None
        self._shutdown_callbacks: List[Callable] = []
    
    async def initialize(self) -> str:
        """Initialize the pool: discover or start server."""
        async with self._lock:
            # Try to discover existing server
            servers = await self.discovery.scan()
            
            # Prefer server on our preferred port
            for server in servers:
                if server.port == self.preferred_port:
                    self._server = server
                    logger.info(f"[POOL] Using existing server at {server.url}")
                    return server.url
            
            # Use any discovered server
            if servers:
                self._server = servers[0]
                logger.info(f"[POOL] Using discovered server at {self._server.url}")
                return self._server.url
            
            # No server found - start one if allowed
            if self.auto_start:
                self._server = await self._start_server()
                if self._server:
                    # Start health monitoring
                    self._health_check_task = asyncio.create_task(self._health_monitor())
                    return self._server.url
            
            raise RuntimeError("No CCT server available and auto_start is disabled")
    
    async def _start_server(self) -> ServerInstance:
        """Start a new CCT server instance."""
        if not self.project_root:
            # Auto-detect project root
            self.project_root = str(Path(__file__).parent.parent.parent)
        
        # Find Python executable
        python_exe = os.path.join(self.project_root, ".venv", "Scripts", "python.exe")
        if not os.path.exists(python_exe):
            python_exe = "python"
        
        main_script = os.path.join(self.project_root, "src", "main.py")
        
        env = os.environ.copy()
        env["CCT_PORT"] = str(self.preferred_port)
        env["CCT_TRANSPORT"] = "sse"
        env["PYTHONPATH"] = self.project_root
        
        logger.info(f"[POOL] Starting CCT server on port {self.preferred_port}...")
        
        process = subprocess.Popen(
            [python_exe, "-u", main_script],
            cwd=self.project_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to be ready
        server = ServerInstance(
            host="localhost",
            port=self.preferred_port,
            url=f"http://localhost:{self.preferred_port}",
            process=process,
            is_managed=True,
            started_at=time.time()
        )
        
        # Poll for startup
        for attempt in range(self.startup_timeout):
            await asyncio.sleep(1)
            
            check = await self.discovery._check_server("localhost", self.preferred_port)
            if check:
                server.is_healthy = True
                server.last_health_check = time.time()
                logger.info(f"[POOL] Server started successfully at {server.url}")
                return server
            
            # Check if process died
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                logger.error(f"[POOL] Server process exited early!\nSTDOUT: {stdout}\nSTDERR: {stderr}")
                raise RuntimeError("CCT server failed to start")
        
        raise RuntimeError("Timeout waiting for CCT server to start")
    
    async def _health_monitor(self):
        """Background task to monitor server health."""
        while self._server and self._server.is_managed:
            await asyncio.sleep(30)
            
            if not self._server:
                break
            
            try:
                check = await self.discovery._check_server(
                    self._server.host,
                    self._server.port
                )
                self._server.is_healthy = check is not None
                self._server.last_health_check = time.time()
            except Exception as e:
                logger.warning(f"[POOL] Health check failed: {e}")
                self._server.is_healthy = False
    
    async def get_server_url(self) -> str:
        """Get the server URL (initializes if needed)."""
        if not self._server:
            await self.initialize()
        return self._server.url if self._server else ""
    
    @asynccontextmanager
    async def get_client(self):
        """Context manager to get a client connection."""
        from mcp import ClientSession
        
        server_url = await self.get_server_url()
        
        # For SSE transport
        try:
            import mcp.client.sse as sse_client
            
            async with sse_client.sse_client(f"{server_url}/cognitive-api/v1/sync") as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    if self._server:
                        self._server.connection_count += 1
                    try:
                        yield session
                    finally:
                        if self._server:
                            self._server.connection_count -= 1
        except ImportError:
            raise RuntimeError("MCP SSE client not available. Install mcp package.")
    
    async def shutdown(self):
        """Shutdown the pool and managed server."""
        async with self._lock:
            # Cancel health monitor
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Terminate managed server
            if self._server and self._server.is_managed and self._server.process:
                logger.info("[POOL] Terminating managed CCT server...")
                self._server.process.terminate()
                try:
                    self._server.process.wait(timeout=5)
                except:
                    self._server.process.kill()
                    self._server.process.wait()
                logger.info("[POOL] Server terminated")
            
            # Call shutdown callbacks
            for callback in self._shutdown_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"[POOL] Shutdown callback error: {e}")
            
            self._server = None
    
    def on_shutdown(self, callback: Callable):
        """Register a callback to be called on shutdown."""
        self._shutdown_callbacks.append(callback)
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()


class SharedCCTClient:
    """Simple client for shared CCT server access."""
    
    def __init__(self, server_url: Optional[str] = None):
        self.server_url = server_url
        self._pool: Optional[CCTServerPool] = None
    
    async def connect(self) -> str:
        """Connect to CCT server (discover or use provided URL)."""
        if self.server_url:
            return self.server_url
        
        # Auto-discover
        self._pool = CCTServerPool(auto_start=False)
        servers = await self._pool.discovery.scan()
        
        if servers:
            self.server_url = servers[0].url
            return self.server_url
        
        raise RuntimeError("No CCT server found. Please start the server first.")
    
    async def think(self, problem: str, strategy: str = "adaptive", profile: str = "balanced") -> Dict[str, Any]:
        """Quick thinking helper."""
        if not self.server_url:
            await self.connect()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/cognitive-api/v1/sessions",
                json={
                    "problem_statement": problem,
                    "thinking_strategy": strategy,
                    "cct_profile": profile
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# Global singleton
_global_pool: Optional[CCTServerPool] = None


async def get_shared_pool() -> CCTServerPool:
    """Get or create the global shared pool."""
    global _global_pool
    
    if _global_pool is None:
        _global_pool = CCTServerPool(auto_start=True)
        await _global_pool.initialize()
    
    return _global_pool


def reset_shared_pool():
    """Reset the global pool (for testing)."""
    global _global_pool
    _global_pool = None


# CLI Interface
async def cli_scan(verbose: bool = False):
    """CLI: Scan for running servers."""
    print("🔍 Scanning for CCT servers...\n")
    
    discovery = CCTServerDiscovery()
    servers = await discovery.scan(verbose=verbose)
    
    if servers:
        print(f"✅ Found {len(servers)} server(s):\n")
        for i, server in enumerate(servers, 1):
            uptime = server.get_uptime()
            uptime_str = f"{uptime:.1f}s" if uptime else "Unknown"
            print(f"  {i}. {server.url}")
            print(f"     Host: {server.host}:{server.port}")
            print(f"     Healthy: {server.is_healthy}")
            print(f"     Uptime: {uptime_str}\n")
    else:
        print("❌ No CCT servers found")
        print("\n💡 Start a server with:")
        print("   python scripts/server/discover.py start")


async def cli_status():
    """CLI: Show detailed status."""
    print("📊 CCT Server Status\n")
    
    discovery = CCTServerDiscovery()
    servers = await discovery.scan(verbose=True)
    
    if servers:
        for server in servers:
            print(f"📍 Server: {server.url}")
            print(f"   Host: {server.host}:{server.port}")
            print(f"   Healthy: {server.is_healthy}")
            print(f"   Uptime: {server.get_uptime():.1f}s" if server.get_uptime() else "   Uptime: Unknown")
            print(f"   Connections: {server.connection_count}")
            print()
    else:
        print("❌ No servers running")


async def cli_health():
    """CLI: Quick health check."""
    discovery = CCTServerDiscovery()
    servers = await discovery.scan()
    
    if servers:
        print("✅ CCT Server is healthy")
        print(f"   URL: {servers[0].url}")
        return 0
    else:
        print("❌ CCT Server is not running")
        return 1


async def cli_start():
    """CLI: Start server if not running."""
    show_banner()
    print("🚀 Starting CCT server pool...\n")
    
    try:
        pool = CCTServerPool(auto_start=True)
        url = await pool.initialize()
        
        print(f"✅ Server started at {url}")
        print("\n📝 Connection Info:")
        print(f"   SSE Endpoint: {url}/cognitive-api/v1/sync")
        print(f"   Health Check: {url}")
        print("\n⚠️  Press Ctrl+C to stop")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            await pool.shutdown()
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return 1


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="CCT Server Discovery and Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/server/discover.py scan       # Scan for servers
  python scripts/server/discover.py start      # Start server
  python scripts/server/discover.py status     # Show status
  python scripts/server/discover.py health      # Health check
        """
    )
    
    parser.add_argument(
        "command",
        choices=["scan", "start", "status", "health"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    commands = {
        "scan": lambda: cli_scan(args.verbose),
        "start": cli_start,
        "status": cli_status,
        "health": cli_health,
    }
    
    try:
        exit_code = asyncio.run(commands[args.command]())
        if exit_code is not None:
            sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
