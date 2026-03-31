# MCP Memory Server

Unified long-term memory for AI agents. Works with Claude Code, Gemini CLI, Codex CLI, or any MCP-compatible tool.

```
Any AI Agent → MCP Tool Call → Memory Server → SQLite (local) + Oracle (cloud, vector search)
```

## Features

- **14 MCP tools** for write, read, delete, search, and admin operations
- **Auto-classifies** memory type (decision, resolved, question, knowledge)
- **Workspace-aware**: auto-detects which project you're in
- **Domain isolation**: work vs personal with cross-domain search when needed
- **Vector search**: semantic similarity via Oracle AI Database VECTOR columns
- **Dual storage**: fast local SQLite + Oracle cloud for cross-workspace queries
- **Works offline**: SQLite always available, Oracle optional

## Quick Start

```bash
# Clone
git clone https://github.com/teddashh/mcp-memory-server.git
cd mcp-memory-server

# Install
pip install -e .

# Configure
python setup_config.py

# Register with Claude Code (~/.claude/.mcp.json)
{
  "mcpServers": {
    "memory": {
      "command": "python",
      "args": ["-X", "utf8", "-m", "mcp_memory"],
      "cwd": "/path/to/mcp-memory-server"
    }
  }
}
```

## MCP Tools

### Write
| Tool | Description |
|------|-------------|
| `memory_store` | Auto-classify and store (decision/resolved/question/knowledge) |
| `memory_record_decision` | Record a decision (what, why, how) |
| `memory_record_resolved` | Record a resolved issue |
| `memory_record_question` | Record an open question (with priority) |
| `memory_record_knowledge` | Record a knowledge item |

### Read
| Tool | Description |
|------|-------------|
| `memory_list` | List recent memories (filter by type) |
| `memory_get` | Get specific memory by ID |
| `memory_get_summary` | Counts per table for a workspace |

### Delete
| Tool | Description |
|------|-------------|
| `memory_delete` | Delete a memory by ID |

### Search
| Tool | Description |
|------|-------------|
| `memory_search` | Semantic vector search across all workspaces (Oracle) |

### Admin
| Tool | Description |
|------|-------------|
| `memory_status` | System overview (local + Oracle + embeddings) |
| `memory_compact` | Check session.md status for compaction |
| `memory_oracle_summary` | Cross-workspace summary from Oracle |

## Architecture

```
Layer 1: session.md          (ephemeral, per-conversation)
Layer 2: SQLite memory.db    (structured, per-workspace)
Layer 3: Obsidian knowledge/  (markdown, shared via git)
Layer 4: Oracle CLAUDE_MEMORY (cloud, cross-workspace, vector search)

MCP Memory Server operates on Layer 2 + Layer 4.
```

## Configuration

Config stored at `~/.mcp-memory/config.json`:

```json
{
  "workspace_root": "~/Documents/Workspace",
  "claude_setup_dir": "~/Documents/claude-setup",
  "workspace_map": "~/Documents/claude-setup/workspace-map.json",
  "oracle": {
    "enabled": true,
    "wallet_dir": "/path/to/wallet",
    "dsn": "(description=...)",
    "user": "CLAUDE_MEMORY",
    "password": "..."
  },
  "embedding": {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "api_key": "sk-..."
  }
}
```

## Transport Modes

```bash
# STDIO (Claude Code, default)
python -m mcp_memory

# HTTP (Gemini CLI, Codex CLI)
python -m mcp_memory --http
# Runs on http://127.0.0.1:8787/mcp
```
