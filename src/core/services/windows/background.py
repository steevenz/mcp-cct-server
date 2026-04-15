"""
CCT Windows Background Service

Core Windows Service implementation for CCT Cognitive OS.
This module contains the actual Windows Service class that runs
as a background Windows Service.

The service launches and monitors the CCT Server subprocess,
providing automatic restart capability and proper service lifecycle management.
"""
from __future__ import annotations

import sys
import os
import time
import logging
import subprocess
import win32serviceutil
import win32service
import win32event
import servicemanager
from pathlib import Path


# Add project root to path
# background.py is at: src/core/services/windows/background.py
# Project root is 5 levels up from this file
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class CCTMCPServerService(win32serviceutil.ServiceFramework):
    """
    Native Windows Service Wrapper for CCT Cognitive OS.
    
    Runs as a Windows Service, launching and monitoring the CCT Server
    subprocess with automatic restart capability.
    """
    _svc_name_ = "CCTMCPServer"
    _svc_display_name_ = "CCT MCP Server"
    _svc_description_ = "Autonomous Cognitive Engine & Local EDR Telemetry Processor."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True
        self.process = None
        
        # Setup headless logging
        log_dir = PROJECT_ROOT / "database" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "cct_service.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
            filename=str(log_file),
            filemode='a'
        )
        self.logger = logging.getLogger("CCTService")

    def SvcStop(self):
        """Handle service stop request."""
        self.logger.info("Service stopping...")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False
        if self.process:
            self.process.terminate()
            self.logger.info("CCT Process terminated.")

    def SvcDoRun(self):
        """Main service entry point."""
        self.logger.info("Service starting...")
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        self.main()

    def _is_port_available(self, port):
        """Check if a port is available for binding."""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
                return True
        except:
            return False
    
    def _find_available_port(self, start_port=8000, max_port=9000):
        """Find an available port in the given range."""
        for port in range(start_port, max_port + 1):
            if self._is_port_available(port):
                return port
        return None

    def main(self):
        """Main service loop - launches and monitors CCT Server."""
        self.logger.info(f"Project Root: {PROJECT_ROOT}")
        
        # Determine Python path (prefer .venv)
        python_exe = sys.executable
        venv_python = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            python_exe = str(venv_python)
            
        self.logger.info(f"Using Python: {python_exe}")
        
        # Determine transport mode and port
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        
        # Get port from environment or use default
        default_port = int(env.get("CCT_PORT", "8000"))
        
        # Check if port is available
        if self._is_port_available(default_port):
            # Port available, use SSE mode
            env["CCT_TRANSPORT"] = "sse"
            self.logger.info(f"Port {default_port} available. Using SSE transport mode.")
        else:
            # Port in use, try to find alternative
            alt_port = self._find_available_port(default_port + 1)
            if alt_port:
                env["CCT_PORT"] = str(alt_port)
                env["CCT_TRANSPORT"] = "sse"
                self.logger.info(f"Port {default_port} in use. Switched to port {alt_port} with SSE transport.")
            else:
                # No available ports, fallback to STDIO mode (no port needed)
                env["CCT_TRANSPORT"] = "stdio"
                self.logger.warning(f"No available ports found. Falling back to STDIO transport mode.")
        
        cmd = [python_exe, "-u", str(PROJECT_ROOT / "src" / "main.py")]
        
        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            self.logger.info(f"CCT Server launched (PID: {self.process.pid})")
            
            # Monitoring loop
            while self.is_running:
                rc = win32event.WaitForSingleObject(self.hWaitStop, 1000)
                if rc == win32event.WAIT_OBJECT_0:
                    break
                
                # Check if process is still alive
                if self.process.poll() is not None:
                    # Log subprocess output before restart
                    if self.process.stdout:
                        output = self.process.stdout.read()
                        if output:
                            self.logger.error(f"CCT Server output:\n{output}")
                    self.logger.warning("CCT Server process died. Attempting restart in 5s...")
                    time.sleep(5)
                    
                    # Re-check port availability before restart
                    current_port = int(env.get("CCT_PORT", "8000"))
                    if not self._is_port_available(current_port):
                        self.logger.warning(f"Port {current_port} still in use. Finding alternative...")
                        alt_port = self._find_available_port(current_port + 1)
                        if alt_port:
                            env["CCT_PORT"] = str(alt_port)
                            env["CCT_TRANSPORT"] = "sse"
                            self.logger.info(f"Switched to port {alt_port} for restart")
                        else:
                            self.logger.warning("No available ports. Falling back to STDIO mode")
                            env["CCT_TRANSPORT"] = "stdio"
                    
                    self.process = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT), env=env)
                    self.logger.info(f"CCT Server restarted (PID: {self.process.pid})")
        
        except Exception as e:
            self.logger.error(f"Fatal error in service: {str(e)}", exc_info=True)


if __name__ == '__main__':
    # Allow this file to be run directly for service installation
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(CCTMCPServerService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(CCTMCPServerService)
