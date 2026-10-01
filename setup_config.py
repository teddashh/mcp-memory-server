"""
Interactive setup for MCP Memory Server.
Run once to configure Oracle connection and embedding provider.

Usage:
    python setup_config.py
"""
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".mcp-memory"
CONFIG_FILE = CONFIG_DIR / "config.json"


def main():
    print("=" * 60)
    print("MCP Memory Server: Setup")
    print("=" * 60)

    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        print(f"\nExisting config found at {CONFIG_FILE}")
        print("Press Enter to keep existing values.\n")

    # Workspace paths
    print("--- Workspace Paths ---")
    ws_root = input(f"Workspace root [{config.get('workspace_root', '~/Documents/Workspace')}]: ").strip()
    if ws_root:
        config["workspace_root"] = ws_root

    cs_dir = input(f"claude-setup dir [{config.get('claude_setup_dir', '~/Documents/claude-setup')}]: ").strip()
    if cs_dir:
        config["claude_setup_dir"] = cs_dir

    # Oracle
    print("\n--- Oracle AI Database (optional) ---")
    oracle_enabled = input(f"Enable Oracle? (y/n) [{('y' if config.get('oracle', {}).get('enabled') else 'n')}]: ").strip().lower()

    if oracle_enabled == "y":
        oracle = config.get("oracle", {})
        oracle["enabled"] = True

        wallet = input(f"Wallet dir [{oracle.get('wallet_dir', '')}]: ").strip()
        if wallet:
            oracle["wallet_dir"] = wallet

        wallet_pwd = input(f"Wallet password [{'****' if oracle.get('wallet_password') else ''}]: ").strip()
        if wallet_pwd:
            oracle["wallet_password"] = wallet_pwd

        dsn = input(f"DSN [{oracle.get('dsn', '')}]: ").strip()
        if dsn:
            oracle["dsn"] = dsn

        user = input(f"User [{oracle.get('user', 'CLAUDE_MEMORY')}]: ").strip()
        if user:
            oracle["user"] = user

        pwd = input(f"Password [{'****' if oracle.get('password') else ''}]: ").strip()
        if pwd:
            oracle["password"] = pwd

        config["oracle"] = oracle
    elif oracle_enabled == "n":
        config.setdefault("oracle", {})["enabled"] = False

    # Embeddings
    print("\n--- Embedding Provider (for semantic search) ---")
    print("Options: none, openai")
    emb = config.get("embedding", {})
    provider = input(f"Provider [{emb.get('provider', 'none')}]: ").strip()
    if provider:
        emb["provider"] = provider

    if emb.get("provider") == "openai":
        key = input(f"OpenAI API key [{'****' if emb.get('api_key') else ''}]: ").strip()
        if key:
            emb["api_key"] = key
        model = input(f"Model [{emb.get('model', 'text-embedding-3-small')}]: ").strip()
        if model:
            emb["model"] = model

    config["embedding"] = emb

    # Save
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n[OK] Config saved to {CONFIG_FILE}")
    print("\nNext: Add to your Claude Code config (~/.claude/.mcp.json):")
    print(json.dumps({
        "mcpServers": {
            "memory": {
                "command": "python",
                "args": ["-X", "utf8", "-m", "mcp_memory"],
                "cwd": str(Path(__file__).parent.resolve()),
            }
        }
    }, indent=2))


if __name__ == "__main__":
    main()
