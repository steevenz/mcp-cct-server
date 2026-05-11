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
import json
import httpx
from pathlib import Path

VERSION = "2.0.0"
PRD_ID = "20260428-x-api-key-resolution"

# Ensure project root is importable when running script from any working directory.
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.security import build_x_api_key_header, ApiKeyResolutionError

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

    project_root = Path(__file__).parent.parent.parent
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
    project_root = Path(__file__).parent.parent.parent
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

    project_root = Path(__file__).parent.parent.parent
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
    pip_upgrade = subprocess.run(
        [str(python_exe), "-m", "pip", "install", "--upgrade", "pip", "--quiet"],
        capture_output=True,
        text=True
    )
    if pip_upgrade.returncode != 0:
        show_status("Syncing Dependencies", "FAILED", "red")
        print(f"  ERROR pip upgrade failed: {pip_upgrade.stderr.strip()}")
        raise RuntimeError("pip upgrade failed")

    pip_install = subprocess.run(
        [str(python_exe), "-m", "pip", "install", "-r", str(requirements), "--quiet"],
        capture_output=True,
        text=True
    )
    if pip_install.returncode != 0:
        show_status("Syncing Dependencies", "FAILED", "red")
        print(f"  ERROR dependency install failed: {pip_install.stderr.strip()}")
        raise RuntimeError("dependency install failed")

    show_status("Syncing Dependencies", "DONE", "green")

def setup_environment():
    """Setup .env file from .env.example if needed."""
    project_root = Path(__file__).parent.parent.parent
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


def install_gemma_models():
    """Ensure local Gemma models (2B/9B) are installed for Local-First operation."""
    show_status("Installing Gemma Models (Local-First)", "CHECKING", "yellow")
    
    try:
        from src.core.llm_offline.engine import get_gemma_engine
        
        # 1. Ensure Gemma 2B (Basic Pattern Extraction)
        engine_2b = get_gemma_engine("2b")
        if not engine_2b.is_available():
            show_status("Downloading Gemma 2B (~1.5GB)", "DOWNLOADING", "yellow")
            # GemmaEngine.__init__ handles download if auto_download=True (default)
            # We just need to trigger it if not available
            engine_2b._download_model()
            show_status("Gemma 2B Installation", "DONE", "green")
        else:
            show_status("Gemma 2B Baseline", "VERIFIED", "cyan")

        # 2. Ensure Gemma 9B (Core Reasoning)
        engine_9b = get_gemma_engine("9b")
        if not engine_9b.is_available():
            show_status("Downloading Gemma 9B (~5GB)", "DOWNLOADING", "yellow")
            engine_9b._download_model()
            show_status("Gemma 9B Installation", "DONE", "green")
        else:
            show_status("Gemma 9B Baseline", "VERIFIED", "cyan")
            
    except Exception as e:
        show_status("Gemma Installation", "FAILED", "red")
        print(f"  WARN  Local Gemma setup failed: {e}")
        print("  INFO  System will fallback to Online APIs if configured.\n")


def _parse_env_value(env_path: Path, key: str) -> str | None:
    """Return value for key from .env-style file, or None when missing."""
    if not env_path.exists() or not env_path.is_file():
        return None
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() != key:
            continue
        parsed = value.strip().strip('"').strip("'")
        return parsed or None
    return None


def _resolve_effective_port(default_port: int, env_path: Path) -> int:
    """Resolve effective server port with precedence: process env > .env > CLI default."""
    env_port = os.getenv("CCT_PORT", "").strip()
    if env_port.isdigit():
        return int(env_port)
    dotenv_port = _parse_env_value(env_path, "CCT_PORT")
    if dotenv_port and dotenv_port.isdigit():
        return int(dotenv_port)
    return default_port


def _detect_active_base_url(preferred_port: int) -> str | None:
    """Best-effort detection of active local CCT server base URL."""
    candidates = [
        f"http://localhost:{preferred_port}",
        f"http://127.0.0.1:{preferred_port}",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ]
    seen: set[str] = set()
    for base_url in candidates:
        if base_url in seen:
            continue
        seen.add(base_url)
        try:
            response = httpx.get(f"{base_url}/status", timeout=2.0)
            if response.status_code != 200:
                continue
            payload = response.json() if "application/json" in response.headers.get("content-type", "") else {}
            if isinstance(payload, dict) and payload.get("server") and payload.get("transport"):
                return base_url
        except Exception:
            continue
    return None


def generate_mcp_client_config(port: int) -> tuple[bool, Path | None]:
    """
    Generate a ready-to-use SSE MCP client config file with automatic X-API-KEY header.
    Returns: (generated, file_path)
    """
    project_root = PROJECT_ROOT
    env_path = project_root / ".env"
    config_dir = project_root / "database" / "config"
    config_path = config_dir / "mcp_client_sse.json"

    effective_port = _resolve_effective_port(default_port=port, env_path=env_path)
    mcp_secret = _parse_env_value(env_path, "CCT_MCP_SECRET")
    mcp_path = f"/sync/{mcp_secret}" if mcp_secret else "/sync"
    active_base = _detect_active_base_url(preferred_port=effective_port)
    base_url = active_base or f"http://localhost:{effective_port}"
    mcp_url = f"{base_url}/cognitive-api/v1{mcp_path}"

    candidates: list[tuple[str, dict[str, str]]] = []
    for source in ("dotenv", "env"):
        try:
            candidates.append(
                (source, build_x_api_key_header(project_root=project_root, source=source))
            )
        except ApiKeyResolutionError:
            continue

    if not candidates:
        show_status("Generating MCP Client Config", "SKIPPED", "yellow")
        print("  WARN  CCT_BOOTSTRAP_API_KEY is not available from .env or process environment.")
        print("  INFO  Set CCT_BOOTSTRAP_API_KEY, then re-run setup to auto-generate config.\n")
        return False, None

    # Use deterministic default (dotenv first), but if server is reachable, auto-pick candidate
    # that returns non-403 for /sync to reduce invalid bootstrap config generation.
    selected_source, headers = candidates[0]
    try:
        import httpx  # Optional runtime probe

        probe_payload = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
        for source, candidate_headers in candidates:
            response = httpx.post(
                mcp_url,
                headers=candidate_headers,
                json=probe_payload,
                timeout=3.0,
            )
            if response.status_code != 403:
                selected_source, headers = source, candidate_headers
                break
    except Exception:
        # No live probe possible (server down or httpx unavailable); keep deterministic default.
        pass

    if selected_source == "env":
        print("  WARN  CCT_BOOTSTRAP_API_KEY loaded from process environment.")
        print("  INFO  If server uses .env key, update .env to avoid auth mismatch.\n")

    payload = {
        "prd_id": PRD_ID,
        "mcpServers": {
            "Creative Critical Thinking": {
                "url": mcp_url,
                "headers": headers
            }
        }
    }

    config_dir.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    show_status("Generating MCP Client Config", "DONE", "green")
    return True, config_path

def configure_multi_agent(port: int = 8001, multi_agent: bool = False):
    """Configure for multi-agent mode."""
    project_root = Path(__file__).parent.parent.parent
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
    project_root = Path(__file__).parent.parent.parent

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
    parser.add_argument("--skip-mcp-config", action="store_true",
                       help="Skip auto generation of SSE MCP client config")

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

    # 8. Generate SSE MCP client config with automatic X-API-KEY header injection
    generated = False
    generated_path: Path | None = None
    if not args.skip_mcp_config:
        generated, generated_path = generate_mcp_client_config(args.port)
        if generated and generated_path:
            print("  MCP CLIENT CONFIG  Auto-generated for SSE mode")
            print(f"  File: {generated_path}")
            print("  Includes: url + X-API-KEY headers\n")

    # 9. Multi-agent info if configured
    if args.multi_agent:
        print("  MULTI-AGENT MODE  Server configured for shared access")
        print("  Quick Start:")
        print("  1. Start server:    .venv/Scripts/python src/main.py" if os.name == 'nt' else "  1. Start server:    .venv/bin/python src/main.py")
        print("  2. Or use manager:   scripts/server/manage.py start")
        print(f"  3. Connect agents:  http://localhost:{args.port}\n")

    # 10. Run server if requested
    if args.run:
        run_server(venv_path, args.multi_agent)
    else:
        if not args.multi_agent:
            python_cmd = ".venv/Scripts/python src/main.py" if os.name == 'nt' else ".venv/bin/python src/main.py"
            print(f"  To start the server, run:")
            print(f"  {python_cmd}\n")

if __name__ == "__main__":
    main()
