#!/bin/bash
# scripts/setup/install_all_mcp.sh
# Universal MCP Installer for CCT MCP Server
# Supports: Windsurf, Trae, AntiGravity, Gemini CLI, Cursor, Claude Desktop, OpenCode

PROJECT_ROOT=$(pwd)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    PROJECT_ROOT=$(cygpath -w "$PROJECT_ROOT")
fi

# Common configuration for all tools
CCT_CONFIG='{
    "command": "npx",
    "args": ["--yes", "--package", "'$PROJECT_ROOT'", "cct-mcp"],
    "env": {
        "CCT_PORT": "8010",
        "CCT_IDE": "universal"
    }
}'

TARGETS=(
    "Windsurf|$HOME/.codeium/windsurf/mcp_config.json|mcpServers"
    "Trae|$HOME/Library/Application Support/Trae/User/mcp.json|mcpServers"
    "Trae Linux|$HOME/.config/Trae/User/mcp.json|mcpServers"
    "AntiGravity|$HOME/.gemini/antigravity/mcp_config.json|mcpServers"
    "Gemini CLI|$HOME/.gemini/mcp_config.json|mcpServers"
    "Cursor|$HOME/Library/Application Support/Cursor/User/globalStorage/heavy-duty-build-it.cursor-chat/mcpServers.json|mcpServers"
    "Cursor Linux|$HOME/.config/Cursor/User/globalStorage/heavy-duty-build-it.cursor-chat/mcpServers.json|mcpServers"
    "Claude Desktop|$HOME/Library/Application Support/Claude/claude_desktop_config.json|mcpServers"
    "Kimi CLI|$HOME/.kimi/config.toml|mcp.servers|TOML"
    "Continue.dev|$HOME/.continue/config.yaml|mcpServers|YAML"
    "Goose|$HOME/Library/Application Support/Goose/config.yaml|mcpServers|YAML"
)

echo -e "\n  \033[43m\033[30m UNIVERSAL MCP INSTALLER \033[0m"
echo -e "  Project: $PROJECT_ROOT\n"

for target in "${TARGETS[@]}"; do
    IFS="|" read -r name path key format <<< "$target"
    
    echo -n "  Checking $name... "
    
    if [ -f "$path" ]; then
        if [[ "$format" == "YAML" || "$format" == "TOML" ]]; then
             echo -e "\033[33m[SEMI-MANUAL - REQUIRES PYTHON HANDLER]\033[0m"
             continue
        fi

        # Use python to update JSON (more reliable than sed/jq for nested structures)
        python3 -c "
import json, os
path = '$path'
try:
    with open(path, 'r') as f:
        data = json.load(f)
except Exception:
    data = {}
if '$key' not in data: data['$key'] = {}
data['$key']['creative-critical-thinking'] = json.loads('$CCT_CONFIG')
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
" && echo -e "\033[32m[UPDATED]\033[0m" || echo -e "\033[31m[ERROR]\033[0m"
    else
        parent_dir=$(dirname "$path")
        if [ -d "$parent_dir" ]; then
            echo -n -e "\033[33m[NOT FOUND - CREATING]\033[0m "
            python3 -c "
import json
path = '$path'
data = {'$key': {'creative-critical-thinking': json.loads('$CCT_CONFIG')}}
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
" && echo -e "\033[32m[DONE]\033[0m" || echo -e "\033[31m[ERROR]\033[0m"
        else
            echo -e "\033[90m[SKIPPED - APP NOT FOUND]\033[0m"
        fi
    fi
done

echo -e "\n  INSTALLATION COMPLETE\n"
echo -e "  NOTE: You may need to restart your IDEs/CLIs for changes to take effect.\n"
