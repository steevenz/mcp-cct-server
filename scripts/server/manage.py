#!/usr/bin/env python
"""
CCT Server Manager - Enhanced Multi-Agent Shared Server Controller

Enhanced version with better error handling and async support.

Author: Steeven Andrian — Senior Systems Architect

Usage:
    python scripts/server/manage.py status          # Check server status
    python scripts/server/manage.py start           # Start shared server
    python scripts/server/manage.py stop            # Stop shared server
    python scripts/server/manage.py restart         # Restart server
    python scripts/server/manage.py logs            # View server logs

Note: For Windows service management, use:
    python scripts/setup/services/windows/service.py install
    python scripts/setup/services/windows/service.py start
    python scripts/setup/services/windows/service.py stop

Environment Variables:
    CCT_PORT - Server port (default: 8001)
    CCT_HOST - Server host (default: 0.0.0.0)
"""
from __future__ import annotations

import sys
import os
import asyncio
import argparse
import subprocess
import time
from pathlib import Path
from typing import Optional

# Add project root and scripts/server to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from discover import CCTServerDiscovery, CCTServerPool

VERSION = "1.0.0"

def show_banner():
    """Display the CCT banner with author info."""
    print(f"\n  CCT COGNITIVE SERVER {VERSION}")
    print("  Crafted By Steeven Andrian Salim - https://github.com/steevenz\n")


class CCTServerManager:
    """Enhanced server manager with better error handling and async support."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or PROJECT_ROOT
        self.port = int(os.getenv("CCT_PORT", "8001"))
        self.discovery = CCTServerDiscovery()
    
    def get_status(self, verbose: bool = False) -> bool:
        """Check if CCT server is running."""
        show_banner()
        print("🔍 Checking CCT server status...")
        
        servers = asyncio.run(self.discovery.scan(verbose=verbose))
        
        if servers:
            print(f"\n✅ CCT Server is RUNNING")
            for s in servers:
                uptime = s.get_uptime()
                uptime_str = f"{uptime:.1f}s" if uptime else "Unknown"
                print(f"   📍 {s.url}")
                print(f"      Port: {s.port}")
                print(f"      Healthy: {s.is_healthy}")
                print(f"      Uptime: {uptime_str}")
                print(f"      Connections: {s.connection_count}")
            print(f"\n   AI Agents can connect to: {servers[0].url}")
            return True
        else:
            print("\n❌ CCT Server is NOT running")
            print("   Start with: python scripts/server/manage.py start")
            return False
    
    def start_server(self, detach: bool = False) -> int:
        """Start CCT server in shared mode."""
        print("🚀 Starting CCT Shared Server...")
        
        # Check if already running
        servers = asyncio.run(self.discovery.scan())
        
        if servers:
            print(f"✅ Server already running at {servers[0].url}")
            return 0
        
        # Start new server
        pool = CCTServerPool(auto_start=True, preferred_port=self.port)
        
        try:
            url = asyncio.run(pool.initialize())
            print(f"\n✅ CCT Server started at {url}")
            print(f"\n📝 Multi-Agent Connection Info:")
            print(f"   SSE Endpoint: {url}/cognitive-api/v1/sync")
            print(f"   Health Check: {url}")
            print(f"   All AI agents should use this URL")
            print(f"\n⚠️  Press Ctrl+C to stop")
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Shutting down...")
                asyncio.run(pool.shutdown())
                return 0
                
        except Exception as e:
            print(f"\n❌ Failed to start server: {e}")
            return 1
    
    def stop_server(self) -> int:
        """Stop running CCT server."""
        show_banner()
        print("🛑 Stopping CCT Server...")
        
        try:
            # Find and kill process on port
            result = subprocess.run(
                ["netstat", "-ano", "|", "findstr", f":{self.port}"],
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split("\n")
                killed_count = 0
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        print(f"   Found process PID: {pid}")
                        subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
                        print(f"   ✅ Stopped process {pid}")
                        killed_count += 1
                
                if killed_count > 0:
                    print(f"\n✅ CCT Server stopped ({killed_count} process(es))")
                    return 0
                else:
                    print("\n⚠️  No CCT server processes found")
                    return 1
            else:
                print("\n⚠️  No CCT server processes found")
                return 1
                
        except Exception as e:
            print(f"⚠️  Error stopping server: {e}")
            return 1
    
    def restart_server(self) -> int:
        """Restart CCT server."""
        show_banner()
        print("🔄 Restarting CCT Server...")
        self.stop_server()
        time.sleep(2)
        return self.start_server()
    
    def view_logs(self, tail: int = 50) -> int:
        """View server logs."""
        show_banner()
        log_path = self.project_root / "database" / "logs" / "cct_service.log"
        
        if not log_path.exists():
            print(f"❌ Log file not found: {log_path}")
            return 1
        
        print(f"📋 Viewing last {tail} lines from {log_path}\n")
        
        try:
            result = subprocess.run(
                ["powershell", "Get-Content", "-Tail", str(tail), "-Wait", str(log_path)],
                # For Windows PowerShell
            )
            return result.returncode
        except KeyboardInterrupt:
            print("\n\n📋 Log viewing stopped")
            return 0
        except Exception as e:
            print(f"❌ Failed to view logs: {e}")
            return 1
    


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CCT Server Manager - Enhanced Multi-Agent Shared Server Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/server/manage.py status
  python scripts/server/manage.py start
  python scripts/server/manage.py stop
  python scripts/server/manage.py restart
  python scripts/server/manage.py logs

For Windows service management:
  python scripts/setup/services/windows/service.py install
  python scripts/setup/services/windows/service.py start
        """
    )
    
    parser.add_argument(
        "command",
        choices=["status", "start", "stop", "restart", "logs"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--tail",
        type=int,
        default=50,
        help="Number of log lines to show (default: 50)"
    )
    
    args = parser.parse_args()
    
    manager = CCTServerManager()
    
    commands = {
        "status": lambda: 0 if manager.get_status(args.verbose) else 1,
        "start": lambda: manager.start_server(),
        "stop": lambda: manager.stop_server(),
        "restart": lambda: manager.restart_server(),
        "logs": lambda: manager.view_logs(args.tail),
    }
    
    try:
        exit_code = commands[args.command]()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
