#!/usr/bin/env python
"""
CCT Server Setup Script

Python equivalent of PowerShell/Bash setup scripts for cross-platform support.

Author: Steeven Andrian — Senior Systems Architect

Usage:
    python scripts/server/setup.py              # Standard setup
    python scripts/server/setup.py --force      # Force recreate .venv and reset database
    python scripts/server/setup.py --skip-deps  # Skip dependency installation
    python scripts/server/setup.py --run        # Start server after setup
    python scripts/server/setup.py --multi-agent # Configure for multi-agent mode
    python scripts/server/setup.py --port 8001   # Set custom port
"""
from __future__ import annotations

import sys
import os
import subprocess
import argparse
from pathlib import Path

VERSION = "2.0.0"

def show_banner():
    """Display the CCT banner with author info."""
    print(f"\n  CCT COGNITIVE SERVER {VERSION}")
    print("  Crafted By Steeven Andrian Salim - https://github.com/steevenz\n")

def show_status(label: str, status: str, color: str = "green"):
    """Display status message with consistent formatting."""
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "cyan": "\033[96m",
        "gray": "\033[90m",
        "reset": "\033[0m"
    }
    colored_status = f"{colors.get(color, '')}{status}{colors['reset']}"
    print(f"  {label.ljust(40, '.')} [{colored_status}]")

def check_python():
    """Check if Python is available."""
    try:
        result = subprocess.run([sys.executable, "--version"], 
                              capture_output=True, text=True)
        show_status(f"Verifying Python Environment ({result.stdout.strip()})", "DONE", "green")
        return True
    except Exception as e:
        show_status("Verifying Python Environment", "FAIL", "red")
        print(f"\n  ERROR: Python is not available.\n")
        return False

def force_cleanup():
    """Force clean architecture - remove .venv and database."""
    show_status("Forcing Clean Architecture", "CLEANING", "yellow")
    
    project_root = Path(__file__).parent.parent
    venv_path = project_root / ".venv"
    db_path = project_root / "cct_memory.db"
    
    if venv_path.exists():
        import shutil
        shutil.rmtree(venv_path)
    if db_path.exists():
        db_path.unlink()
    
    show_status("Forcing Clean Architecture", "CLEAN", "green")

def setup_virtual_environment():
    """Create or verify virtual environment."""
    project_root = Path(__file__).parent.parent
    venv_path = project_root / ".venv"
    
    if not venv_path.exists():
        show_status("Managing Virtual Environment", "CREATING", "yellow")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], 
                      cwd=project_root)
        show_status("Managing Virtual Environment", "DONE", "green")
    else:
        show_status("Managing Virtual Environment", "EXISTING", "cyan")
    
    return venv_path

def install_dependencies(venv_path: Path, skip: bool = False):
    """Install Python dependencies."""
    if skip:
        show_status("Syncing Dependencies", "SKIPPED", "cyan")
        return
    
    show_status("Syncing Dependencies", "SYNCING", "yellow")
    
    project_root = Path(__file__).parent.parent
    requirements = project_root / "requirements.txt"
    
    if not requirements.exists():
        show_status("Syncing Dependencies", "MISSING", "red")
        return
    
    # Determine python executable in venv
    if os.name == 'nt':  # Windows
        python_exe = venv_path / "Scripts" / "python.exe"
    else:  # Unix-like
        python_exe = venv_path / "bin" / "python"
    
    # Upgrade pip and install requirements
    subprocess.run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip", 
                   "--quiet"], capture_output=True)
    subprocess.run([str(python_exe), "-m", "pip", "install", "-r", 
                   str(requirements), "--quiet"], capture_output=True)
    
    show_status("Syncing Dependencies", "DONE", "green")

def setup_environment():
    """Setup .env file from .env.example if needed."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    show_status("Auditing Configuration (.env)", "AUDITING", "yellow")
    
    if not env_file.exists():
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            show_status("Auditing Configuration (.env)", "INITIALIZED", "green")
        else:
            show_status("Auditing Configuration (.env)", "FAILED", "red")
    else:
        show_status("Auditing Configuration (.env)", "VERIFIED", "cyan")

def configure_multi_agent(port: int = 8001, multi_agent: bool = False):
    """Configure for multi-agent mode."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if not multi_agent and port == 8001:
        return
    
    show_status("Configuring Multi-Agent Server", "CONFIGURING", "yellow")
    
    # Read existing .env
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
    else:
        env_content = ""
    
    # Update port
    if "CCT_PORT=" in env_content:
        env_content = env_content.replace(
            f"CCT_PORT={env_content.split('CCT_PORT=')[1].split('\\n')[0]}",
            f"CCT_PORT={port}"
        )
    else:
        env_content += f"\nCCT_PORT={port}"
    
    # Set transport to SSE for multi-agent
    if multi_agent:
        if "CCT_TRANSPORT=" in env_content:
            env_content = env_content.replace(
                f"CCT_TRANSPORT={env_content.split('CCT_TRANSPORT=')[1].split('\\n')[0]}",
                "CCT_TRANSPORT=sse"
            )
        else:
            env_content += "\nCCT_TRANSPORT=sse"
    
    # Save updated .env
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    show_status("Configuring Multi-Agent Server", f"PORT={port}", "green")

def run_server(venv_path: Path, multi_agent: bool = False):
    """Run the CCT server."""
    project_root = Path(__file__).parent.parent
    
    # Determine python executable in venv
    if os.name == 'nt':  # Windows
        python_exe = venv_path / "Scripts" / "python.exe"
    else:  # Unix-like
        python_exe = venv_path / "bin" / "python"
    
    print("  INFO  Launching Cognitive Engine...\n")
    
    # Run the server
    subprocess.run([str(python_exe), "src/main.py"], cwd=project_root)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CCT Server Setup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/server/setup.py              # Standard setup
  python scripts/server/setup.py --force      # Force recreate .venv
  python scripts/server/setup.py --skip-deps  # Skip dependencies
  python scripts/server/setup.py --run        # Start after setup
  python scripts/server/setup.py --multi-agent # Multi-agent mode
  python scripts/server/setup.py --port 8001   # Custom port
        """
    )
    
    parser.add_argument("--force", action="store_true", 
                       help="Force recreate .venv and reset database")
    parser.add_argument("--skip-deps", action="store_true",
                       help="Skip dependency installation")
    parser.add_argument("--run", action="store_true",
                       help="Start server after setup")
    parser.add_argument("--multi-agent", action="store_true",
                       help="Configure for multi-agent mode")
    parser.add_argument("--port", type=int, default=8001,
                       help="Server port (default: 8001)")
    
    args = parser.parse_args()
    
    show_banner()
    
    # 1. Check Python
    if not check_python():
        sys.exit(1)
    
    # 2. Force cleanup if requested
    if args.force:
        force_cleanup()
    
    # 3. Setup virtual environment
    venv_path = setup_virtual_environment()
    
    # 4. Install dependencies
    install_dependencies(venv_path, args.skip_deps)
    
    # 5. Setup environment
    setup_environment()
    
    # 6. Configure multi-agent if requested
    configure_multi_agent(args.port, args.multi_agent)
    
    # 7. Success message
    print("\n  SUCCESS  Mission Ready: CCT MCP Server is initialized.\n")
    
    # 8. Multi-agent info if configured
    if args.multi_agent:
        print("  MULTI-AGENT MODE  Server configured for shared access")
        print("  Quick Start:")
        print("  1. Start server:    .venv/Scripts/python src/main.py" if os.name == 'nt' else "  1. Start server:    .venv/bin/python src/main.py")
        print("  2. Or use manager:   scripts/server/manage.py start")
        print(f"  3. Connect agents:  http://localhost:{args.port}\n")
    
    # 9. Run server if requested
    if args.run:
        run_server(venv_path, args.multi_agent)
    else:
        if not args.multi_agent:
            python_cmd = ".venv/Scripts/python src/main.py" if os.name == 'nt' else ".venv/bin/python src/main.py"
            print(f"  To start the server, run:")
            print(f"  {python_cmd}\n")

if __name__ == "__main__":
    main()
