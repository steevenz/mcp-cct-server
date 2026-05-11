import os
import sys
import json
import platform
import logging
from pathlib import Path

# Ensure project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.setup.mcp_config_helper import update_json

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("mcp-register")

PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
PACKAGE_JSON_PATH = PROJECT_ROOT / "package.json"

def get_mcp_config(ide="cursor"):
    """Build the MCP configuration for a specific IDE."""
    # We use npx to run the wrapper. 
    # The wrapper will manage the single Python process.
    return {
        "command": "npx",
        "args": [
            "-y",
            "--package",
            str(PROJECT_ROOT),
            "cct-mcp",
            "--ide",
            ide
        ],
        "env": {
            "CCT_IDE": ide
        }
    }

def register_mcp():
    is_windows = platform.system() == "Windows"
    user_home = Path.home()
    
    configs = []
    
    # 1. Claude Desktop
    if is_windows:
        claude_path = user_home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    else:
        claude_path = user_home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    
    if claude_path.parent.exists():
        configs.append((claude_path, "mcpServers", get_mcp_config("claude")))

    # 2. Cursor
    if is_windows:
        cursor_path = user_home / "AppData" / "Roaming" / "Cursor" / "User" / "globalStorage" / "moosefish.cursor-mcp" / "mcpServers.json"
    else:
        cursor_path = user_home / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / "moosefish.cursor-mcp" / "mcpServers.json"
        
    # Alternate Cursor path (Windsurf / others might use similar)
    if not cursor_path.parent.exists():
         # Fallback to standard VSCode location for some MCP extensions
         cursor_path = user_home / ".cursor" / "mcpServers.json"

    if cursor_path.parent.exists() or cursor_path.exists():
        configs.append((cursor_path, "mcpServers", get_mcp_config("cursor")))

    # 3. Windsurf
    windsurf_path = user_home / ".codeium" / "windsurf" / "mcp_config.json"
    if windsurf_path.parent.exists():
        configs.append((windsurf_path, "mcpServers", get_mcp_config("windsurf")))

    # Apply configs
    for path, key, config in configs:
        logger.info(f"Registering CCT in {path}...")
        
        # Create config file if it doesn't exist
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({key: {}}, f, indent=2)
        
        # Use helper to update
        if update_json(str(path), key, config):
            logger.info(f"Successfully registered in {path}")
        else:
            logger.error(f"Failed to register in {path}")

if __name__ == "__main__":
    register_mcp()
