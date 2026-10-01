"""
Database layer: SQLite (local) + Oracle (cloud).
"""
import json
import os
import sqlite3
import uuid
from pathlib import Path

from .config import load_config


# ============================================================
# Workspace detection
# ============================================================

def detect_workspace() -> str:
    """Detect current workspace from cwd or env."""
    ws = os.environ.get("MEMORY_WORKSPACE")
    if ws:
        return ws

    config = load_config()
    cwd = Path(os.environ.get("INIT_CWD", os.getcwd()))

    if "claude-setup" in str(cwd):
        return "claude-setup"

    try:
        with open(config["workspace_map"]) as f:
            ws_map = json.load(f)
        ws_root = Path(config["workspace_root"])
        for ws_id, display_path in ws_map.items():
            ws_path = ws_root / display_path
            try:
                if cwd == ws_path or ws_path in cwd.parents or cwd in ws_path.parents:
                    return ws_id
            except (ValueError, OSError):
                continue
    except FileNotFoundError:
        pass

    return "unknown"


# ============================================================
# SQLite
# ============================================================

def get_sqlite(workspace_id: str = None) -> sqlite3.Connection:
    """Get SQLite connection for a workspace."""
    ws_id = workspace_id or detect_workspace()
    config = load_config()

    if ws_id == "claude-setup":
        db_path = Path(config["claude_setup_dir"]) / ".claude-memory" / "memory.db"
    else:
        try:
            with open(config["workspace_map"]) as f:
                ws_map = json.load(f)
            if ws_id in ws_map:
                db_path = Path(config["workspace_root"]) / ws_map[ws_id] / ".claude-memory" / "memory.db"
            else:
                raise FileNotFoundError(f"Workspace '{ws_id}' not in workspace-map.json")
        except FileNotFoundError:
            raise

    if not db_path.exists():
        raise FileNotFoundError(f"memory.db not found at {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def new_id() -> str:
    return str(uuid.uuid4())[:8]


def tags_to_json(tags: str) -> str:
    return json.dumps([t.strip() for t in tags.split(",") if t.strip()])


# ============================================================
# Oracle
# ============================================================

_oracle_conn = None


def get_oracle():
    """Get Oracle connection (cached). Returns None if not configured."""
    global _oracle_conn
    config = load_config()

    if not config["oracle"]["enabled"]:
        return None

    if _oracle_conn is not None:
        try:
            _oracle_conn.ping()
            return _oracle_conn
        except Exception:
            _oracle_conn = None

    import oracledb
    _oracle_conn = oracledb.connect(
        user=config["oracle"]["user"],
        password=config["oracle"]["password"],
        dsn=config["oracle"]["dsn"],
        config_dir=config["oracle"]["wallet_dir"],
        wallet_location=config["oracle"]["wallet_dir"],
        wallet_password=config["oracle"]["wallet_password"],
        tcp_connect_timeout=15,
    )
    return _oracle_conn
