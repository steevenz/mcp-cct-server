"""
Native Windows Service Wrapper for CCT Cognitive OS
"""
from __future__ import annotations

import os
import sys
import time
import logging
import subprocess
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket

# Ensure we can find src
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

class CCTCognitiveOSService(win32serviceutil.ServiceFramework):
    _svc_name_ = "CCTCognitiveOS"
    _svc_display_name_ = "CCT Cognitive OS Engine"
    _svc_description_ = "Autonomous Cognitive Engine & Local EDR Telemetry Processor."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True
        self.process = None
        
        # Setup headless logging
        log_dir = os.path.join(PROJECT_ROOT, "database", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "cct_service.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
            filename=log_file,
            filemode='a'
        )
        self.logger = logging.getLogger("CCTService")

    def SvcStop(self):
        self.logger.info("Service stopping...")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False
        if self.process:
            self.process.terminate()
            self.logger.info("CCT Process terminated.")

    def SvcDoRun(self):
        self.logger.info("Service starting...")
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        self.main()

    def main(self):
        self.logger.info(f"Project Root: {PROJECT_ROOT}")
        
        # Determine Python path (prefer .venv)
        python_exe = sys.executable
        venv_python = os.path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe")
        if os.path.exists(venv_python):
            python_exe = venv_python
            
        self.logger.info(f"Using Python: {python_exe}")
        
        # Launch CCT Server as a subprocess
        # We force CCT_TRANSPORT=sse for headless operation
        env = os.environ.copy()
        env["CCT_TRANSPORT"] = "sse"
        env["PYTHONPATH"] = PROJECT_ROOT
        
        cmd = [python_exe, "-u", os.path.join(PROJECT_ROOT, "src", "main.py")]
        
        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=PROJECT_ROOT,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            self.logger.info(f"CCT Server launched (PID: {self.process.pid})")
            
            # Monitoring loop
            while self.is_running:
                # Check for stop event
                rc = win32event.WaitForSingleObject(self.hWaitStop, 1000)
                if rc == win32event.WAIT_OBJECT_0:
                    break
                
                # Check if process is still alive
                if self.process.poll() is not None:
                    self.logger.warning("CCT Server process died. Attempting restart in 5s...")
                    time.sleep(5)
                    self.process = subprocess.Popen(cmd, cwd=PROJECT_ROOT, env=env)
        
        except Exception as e:
            self.logger.error(f"Fatal error in service: {str(e)}", exc_info=True)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(CCTCognitiveOSService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(CCTCognitiveOSService)
