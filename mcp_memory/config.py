"""
Configuration management for MCP Memory Server.
Reads from ~/.mcp-memory/config.json or environment variables.
"""
import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".mcp-memory"
CONFIG_FILE = CONFIG_DIR / "config.json"

_DEFAULT = {
    "workspace_root": str(Path.home() / "Documents" / "Workspace"),
    "claude_setup_dir": str(Path.home() / "Documents" / "claude-setup"),
    "workspace_map": str(Path.home() / "Documents" / "claude-setup" / "workspace-map.json"),
    "knowledge_dir": str(Path.home() / "Documents" / "knowledge"),
    "oracle": {
        "enabled": False,
        "wallet_dir": "",
        "wallet_password": "",
        "dsn": "",
        "user": "CLAUDE_MEMORY",
        "password": "",
    },
    "embedding": {
        "provider": "none",
        "model": "text-embedding-3-small",
        "api_key": "",
    },
}


def load_config() -> dict:
    """Load config from file, merge with defaults."""
    config = _DEFAULT.copy()

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            user_config = json.load(f)
        _deep_merge(config, user_config)

    # Env overrides
    if os.environ.get("MCP_MEMORY_WORKSPACE_ROOT"):
        config["workspace_root"] = os.environ["MCP_MEMORY_WORKSPACE_ROOT"]
    if os.environ.get("MCP_MEMORY_ORACLE_PASSWORD"):
        config["oracle"]["password"] = os.environ["MCP_MEMORY_ORACLE_PASSWORD"]
    if os.environ.get("OPENAI_API_KEY"):
        config["embedding"]["api_key"] = os.environ["OPENAI_API_KEY"]

    return config


def save_config(config: dict):
    """Save config to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def _deep_merge(base: dict, override: dict):
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
