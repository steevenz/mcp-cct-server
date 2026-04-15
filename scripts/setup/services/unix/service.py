#!/usr/bin/env python
"""
CCT Linux/macOS Service Management

CLI for managing the CCT systemd/Linux service or launchd/macOS service.
Provides service installation, lifecycle management, and status checking.

Author: Steeven Andrian — Senior Systems Architect

Management CLI:
    python scripts/setup/services/unix/service.py install
    python scripts/setup/services/unix/service.py start
    python scripts/setup/services/unix/service.py stop
    python scripts/setup/services/unix/service.py remove
"""
from __future__ import annotations

import sys
import os
import subprocess
import argparse
import platform
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# Platform Detection
# ============================================================================

def get_platform() -> str:
    """Detect the current platform."""
    system = platform.system().lower()
    if system == "linux":
        return "linux"
    elif system == "darwin":
        return "macos"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


# ============================================================================
# Linux Service Manager (systemd)
# ============================================================================

class LinuxServiceManager:
    """Manages CCT systemd service on Linux."""
    
    SERVICE_NAME = "cct-cognitive-os"
    SERVICE_FILE = "/etc/systemd/system/cct-cognitive-os.service"
    
    def __init__(self, project_root: str | None = None):
        self.project_root = Path(project_root) if project_root else PROJECT_ROOT
        self.python_exe = self._find_python()
        self.venv_python = self.project_root / ".venv" / "bin" / "python"
    
    def _find_python(self) -> str:
        """Find Python executable, preferring venv."""
        if self.venv_python.exists():
            return str(self.venv_python)
        return sys.executable
    
    def _generate_service_file(self) -> str:
        """Generate systemd service file content."""
        return f"""[Unit]
Description=CCT Cognitive OS Engine
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'root')}
WorkingDirectory={self.project_root}
ExecStart={self.python_exe} -m src.main
Restart=always
RestartSec=10
Environment="PYTHONPATH={self.project_root}"
Environment="CCT_TRANSPORT=sse"
Environment="CCT_HOST=0.0.0.0"
Environment="CCT_PORT=8001"

[Install]
WantedBy=multi-user.target
"""
    
    def check_root(self) -> bool:
        """Check if running with root privileges."""
        return os.geteuid() == 0
    
    def install(self) -> bool:
        """Install CCT as systemd service."""
        if not self.check_root():
            print("❌ ERROR: Root privileges required")
            print("   Please run with sudo")
            return False
        
        print("🔧 Installing CCT as systemd service...")
        print(f"   Project Root: {self.project_root}")
        print(f"   Python: {self.python_exe}")
        
        try:
            # Generate service file
            service_content = self._generate_service_file()
            
            # Write service file
            with open(self.SERVICE_FILE, 'w') as f:
                f.write(service_content)
            
            print(f"   Service file written to: {self.SERVICE_FILE}")
            
            # Reload systemd
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            
            # Enable service
            subprocess.run(['systemctl', 'enable', self.SERVICE_NAME], check=True)
            
            print("\n✅ Service installed successfully")
            print(f"   Service Name: {self.SERVICE_NAME}")
            print(f"   Start with: sudo systemctl start {self.SERVICE_NAME}")
            print(f"   Enable at boot: sudo systemctl enable {self.SERVICE_NAME}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to install service: {e}")
            return False
    
    def start(self) -> bool:
        """Start the systemd service."""
        print(f"🚀 Starting {self.SERVICE_NAME} service...")
        
        try:
            subprocess.run(['systemctl', 'start', self.SERVICE_NAME], check=True)
            print(f"\n✅ Service started")
            print("   All AI agents can now connect to http://localhost:8001")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start service: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the systemd service."""
        print(f"🛑 Stopping {self.SERVICE_NAME} service...")
        
        try:
            subprocess.run(['systemctl', 'stop', self.SERVICE_NAME], check=True)
            print("\n✅ Service stopped")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to stop service: {e}")
            return False
    
    def status(self) -> bool:
        """Check service status."""
        try:
            result = subprocess.run(
                ['systemctl', 'status', self.SERVICE_NAME],
                capture_output=True,
                text=True
            )
            
            print(f"\n📊 {self.SERVICE_NAME} Status:")
            print(result.stdout)
            return "active (running)" in result.stdout or "running" in result.stdout.lower()
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Service not installed or failed to query: {e}")
            return False
    
    def remove(self) -> bool:
        """Remove the systemd service."""
        if not self.check_root():
            print("❌ ERROR: Root privileges required")
            return False
        
        print(f"🗑️  Removing {self.SERVICE_NAME} service...")
        
        # Stop first if running
        self.stop()
        
        try:
            # Disable service
            subprocess.run(['systemctl', 'disable', self.SERVICE_NAME], 
                         capture_output=True)
            
            # Remove service file
            if os.path.exists(self.SERVICE_FILE):
                os.remove(self.SERVICE_FILE)
            
            # Reload systemd
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            
            print("\n✅ Service removed")
            return True
            
        except Exception as e:
            print(f"❌ Failed to remove service: {e}")
            return False
    
    def restart(self) -> bool:
        """Restart the systemd service."""
        print(f"🔄 Restarting {self.SERVICE_NAME} service...")
        self.stop()
        import time
        time.sleep(2)
        return self.start()


# ============================================================================
# macOS Service Manager (launchd)
# ============================================================================

class MacOSServiceManager:
    """Manages CCT launchd service on macOS."""
    
    PLIST_NAME = "com.cct.cognitiveos"
    PLIST_PATH = f"/Library/LaunchDaemons/{PLIST_NAME}.plist"
    
    def __init__(self, project_root: str | None = None):
        self.project_root = Path(project_root) if project_root else PROJECT_ROOT
        self.python_exe = self._find_python()
        self.venv_python = self.project_root / ".venv" / "bin" / "python"
    
    def _find_python(self) -> str:
        """Find Python executable, preferring venv."""
        if self.venv_python.exists():
            return str(self.venv_python)
        return sys.executable
    
    def _generate_plist(self) -> str:
        """Generate launchd plist content."""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{self.PLIST_NAME}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>{self.python_exe}</string>
        <string>-m</string>
        <string>src.main</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>{self.project_root}</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>{self.project_root}/database/logs/cct_service.log</string>
    
    <key>StandardErrorPath</key>
    <string>{self.project_root}/database/logs/cct_service_error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>{self.project_root}</string>
        <key>CCT_TRANSPORT</key>
        <string>sse</string>
        <key>CCT_HOST</key>
        <string>0.0.0.0</string>
        <key>CCT_PORT</key>
        <string>8001</string>
    </dict>
</dict>
</plist>
"""
    
    def check_root(self) -> bool:
        """Check if running with root privileges."""
        return os.geteuid() == 0
    
    def install(self) -> bool:
        """Install CCT as launchd service."""
        if not self.check_root():
            print("❌ ERROR: Root privileges required")
            print("   Please run with sudo")
            return False
        
        print("🔧 Installing CCT as launchd service...")
        print(f"   Project Root: {self.project_root}")
        print(f"   Python: {self.python_exe}")
        
        try:
            # Generate plist
            plist_content = self._generate_plist()
            
            # Write plist file
            with open(self.PLIST_PATH, 'w') as f:
                f.write(plist_content)
            
            print(f"   Plist written to: {self.PLIST_PATH}")
            
            # Load the service
            subprocess.run(['launchctl', 'load', self.PLIST_PATH], check=True)
            
            print("\n✅ Service installed successfully")
            print(f"   Service Name: {self.PLIST_NAME}")
            print(f"   Start with: sudo launchctl start {self.PLIST_NAME}")
            print(f"   Stop with: sudo launchctl stop {self.PLIST_NAME}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to install service: {e}")
            return False
    
    def start(self) -> bool:
        """Start the launchd service."""
        print(f"🚀 Starting {self.PLIST_NAME} service...")
        
        try:
            subprocess.run(['launchctl', 'start', self.PLIST_NAME], check=True)
            print(f"\n✅ Service started")
            print("   All AI agents can now connect to http://localhost:8001")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start service: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the launchd service."""
        print(f"🛑 Stopping {self.PLIST_NAME} service...")
        
        try:
            subprocess.run(['launchctl', 'stop', self.PLIST_NAME], check=True)
            print("\n✅ Service stopped")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to stop service: {e}")
            return False
    
    def status(self) -> bool:
        """Check service status."""
        try:
            result = subprocess.run(
                ['launchctl', 'list', self.PLIST_NAME],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"\n📊 {self.PLIST_NAME} Status:")
                print(result.stdout)
                return True
            else:
                print(f"❌ Service not installed")
                return False
                
        except Exception as e:
            print(f"❌ Failed to query service: {e}")
            return False
    
    def remove(self) -> bool:
        """Remove the launchd service."""
        if not self.check_root():
            print("❌ ERROR: Root privileges required")
            return False
        
        print(f"🗑️  Removing {self.PLIST_NAME} service...")
        
        # Stop first if running
        self.stop()
        
        try:
            # Unload the service
            subprocess.run(['launchctl', 'unload', self.PLIST_PATH], 
                         capture_output=True)
            
            # Remove plist file
            if os.path.exists(self.PLIST_PATH):
                os.remove(self.PLIST_PATH)
            
            print("\n✅ Service removed")
            return True
            
        except Exception as e:
            print(f"❌ Failed to remove service: {e}")
            return False
    
    def restart(self) -> bool:
        """Restart the launchd service."""
        print(f"🔄 Restarting {self.PLIST_NAME} service...")
        self.stop()
        import time
        time.sleep(2)
        return self.start()


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CCT Linux/macOS Service Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup/services/unix/service.py install
  python scripts/setup/services/unix/service.py start
  python scripts/setup/services/unix/service.py stop
  python scripts/setup/services/unix/service.py restart
  python scripts/setup/services/unix/service.py remove
  python scripts/setup/services/unix/service.py status

Linux (systemd):
  Requires sudo for install/remove operations
  Service runs as systemd service

macOS (launchd):
  Requires sudo for install/remove operations
  Service runs as launchd daemon
        """
    )
    
    parser.add_argument(
        "command",
        choices=["install", "start", "stop", "restart", "remove", "status"],
        help="Service command"
    )
    
    args = parser.parse_args()
    
    # Get platform-specific manager
    try:
        platform_name = get_platform()
        if platform_name == "linux":
            manager = LinuxServiceManager()
        elif platform_name == "macos":
            manager = MacOSServiceManager()
        else:
            print(f"❌ Unsupported platform: {platform_name}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Platform detection failed: {e}")
        sys.exit(1)
    
    # Execute command
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


if __name__ == '__main__':
    main()
