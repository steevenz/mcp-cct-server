#!/usr/bin/env python
"""
CCT Windows Service Management

CLI for managing the CCT Windows Service.
The actual Windows Service implementation is in src/core/services/windows/background.py

Author: Steeven Andrian — Senior Systems Architect

Management CLI:
    python scripts/setup/services/windows/service.py install
    python scripts/setup/services/windows/service.py start
    python scripts/setup/services/windows/service.py stop
    python scripts/setup/services/windows/service.py remove
"""
from __future__ import annotations

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# Windows Service Manager
# ============================================================================

class WindowsServiceManager:
    """Manages CCT Windows Service installation and lifecycle."""
    
    SERVICE_NAME = "CCTMCPServer"
    SERVICE_DISPLAY_NAME = "CCT MCP Server"
    
    def __init__(self, project_root: str | None = None):
        self.project_root = Path(project_root) if project_root else PROJECT_ROOT
        self.service_script = self.project_root / "src" / "core" / "services" / "windows" / "background.py"
        self.python_exe = self._find_python()
    
    def _find_python(self) -> str:
        """Find Python executable, preferring venv."""
        venv_python = self.project_root / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            return str(venv_python)
        return sys.executable
    
    def check_admin(self) -> bool:
        """Check if running with administrator privileges."""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def install(self) -> bool:
        """Install CCT as Windows Service."""
        if not self.check_admin():
            print("❌ ERROR: Administrator privileges required")
            print("   Please run as Administrator")
            return False
        
        print("🔧 Installing CCT as Windows Service...")
        print(f"   Project Root: {self.project_root}")
        print(f"   Python: {self.python_exe}")
        print(f"   Service Script: {self.service_script}")
        
        if not self.service_script.exists():
            print(f"❌ Service script not found: {self.service_script}")
            return False
        
        try:
            # Install service using pywin32 (this file itself)
            result = subprocess.run(
                [self.python_exe, str(self.service_script), "install"],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            print(result.stdout)
            if result.returncode != 0:
                print(result.stderr)
                return False
            
            # Configure service startup type (auto-start on boot)
            print("\n🔧 Configuring auto-startup on boot...")
            subprocess.run([
                "sc.exe", "config", self.SERVICE_NAME,
                "start=", "auto"
            ], capture_output=True, check=False)
            
            # Configure service recovery options (restart on failure)
            print("\n🔧 Configuring service recovery options...")
            subprocess.run([
                "sc.exe", "failure", self.SERVICE_NAME,
                "reset=", "86400",
                "actions=", "restart/60000/restart/60000/restart/60000"
            ], capture_output=True, check=False)
            
            print("\n✅ Service installed successfully")
            print(f"   Startup Type: Automatic (runs on Windows boot)")
            print(f"   Service Name: {self.SERVICE_NAME}")
            print(f"   Start with: python scripts/server/manage.py service-start")
            print(f"   Or: sc start {self.SERVICE_NAME}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to install service: {e}")
            return False
    
    def start(self) -> bool:
        """Start the Windows Service."""
        print(f"🚀 Starting {self.SERVICE_NAME} service...")
        
        try:
            result = subprocess.run(
                ["sc.exe", "start", self.SERVICE_NAME],
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            if result.returncode == 0 or "START_PENDING" in result.stdout or "RUNNING" in result.stdout:
                print(f"\n✅ Service started")
                print("   All AI agents can now connect to http://localhost:8001")
                return True
            else:
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Failed to start service: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the Windows Service."""
        print(f"🛑 Stopping {self.SERVICE_NAME} service...")
        
        try:
            result = subprocess.run(
                ["sc.exe", "stop", self.SERVICE_NAME],
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            if result.returncode == 0 or "STOP_PENDING" in result.stdout or "STOPPED" in result.stdout:
                print("\n✅ Service stopped")
                return True
            else:
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Failed to stop service: {e}")
            return False
    
    def status(self) -> bool:
        """Check service status."""
        try:
            result = subprocess.run(
                ["sc.exe", "query", self.SERVICE_NAME],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"\n📊 {self.SERVICE_NAME} Status:")
                print(result.stdout)
                return "RUNNING" in result.stdout
            else:
                print(f"❌ Service not installed")
                return False
                
        except Exception as e:
            print(f"❌ Failed to query service: {e}")
            return False
    
    def remove(self) -> bool:
        """Remove the Windows Service."""
        if not self.check_admin():
            print("❌ ERROR: Administrator privileges required")
            return False
        
        print(f"🗑️  Removing {self.SERVICE_NAME} service...")
        
        # Stop first if running
        self.stop()
        
        try:
            result = subprocess.run(
                [self.python_exe, str(self.service_script), "remove"],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            print(result.stdout)
            if result.returncode == 0:
                print("\n✅ Service removed")
                return True
            else:
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Failed to remove service: {e}")
            return False
    
    def restart(self) -> bool:
        """Restart the Windows Service."""
        print(f"🔄 Restarting {self.SERVICE_NAME} service...")
        self.stop()
        import time
        time.sleep(2)
        return self.start()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CCT Windows Service Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup/services/windows/service.py install
  python scripts/setup/services/windows/service.py start
  python scripts/setup/services/windows/service.py stop
  python scripts/setup/services/windows/service.py restart
  python scripts/setup/services/windows/service.py remove
        """
    )
    
    parser.add_argument(
        "command",
        choices=["install", "start", "stop", "restart", "remove", "status"],
        help="Service command"
    )
    
    args = parser.parse_args()
    
    manager = WindowsServiceManager()
    
    commands = {
        "install": manager.install,
        "start": manager.start,
        "stop": manager.stop,
        "restart": manager.restart,
        "remove": manager.remove,
        "status": manager.status,
    }
    
    success = commands[args.command]()
    sys.exit(0 if success else 1)


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == '__main__':
    main()
