# MCP Memory Server

**Every interaction leaves a trace. Every trace becomes knowledge.**

A unified long-term memory and knowledge base system for AI agents. One MCP server, every tool, every workspace — nothing gets lost.

```
Any AI Agent ──→ MCP Tool Call ──→ Memory Server ──→ Local DB + Cloud DB (vector search)
                 (native)          (auto-detect       (structured + semantic)
                                    workspace)
```

## Why This Exists

AI agents are stateless. They forget everything between sessions. Your decisions, your solved problems, your hard-won knowledge — gone.

**MCP Memory Server fixes this.** It gives every AI agent a structured, searchable, persistent memory that:

- **Remembers decisions** — what you chose, why, and how
- **Tracks resolved issues** — so you never solve the same bug twice
- **Keeps open questions** — prioritized, never lost in chat history
- **Builds a knowledge base** — every insight, automatically catalogued
- **Searches semantically** — find memories by meaning, not just keywords
- **Works across projects** — isolated by default, cross-searchable when needed
- **Separates work and personal** — domain boundaries with opt-in cross-domain search

## How It Works

```
┌─ Claude Code (workspace 1) ──┐
├─ Claude Code (workspace 2) ──┤
├─ Gemini CLI ─────────────────┼──→ MCP Memory Server
├─ Codex CLI ──────────────────┤         │
└─ Any MCP Client ─────────────┘         ├── Local SQLite (fast, always available)
                                         ├── Cloud DB (cross-workspace, vector search)
                                         └── Knowledge files (markdown, git-synced)
```

**Zero-config for basic use.** Install, register, done. SQLite works out of the box.

**Cloud DB is optional.** Add Oracle, PostgreSQL, or any DB backend for cross-workspace queries and vector search.

## Quick Start

```bash
# Clone
git clone https://github.com/teddashh/mcp-memory-server.git
cd mcp-memory-server

# Install
pip install -e .

# Configure (optional — works with defaults)
python setup_config.py
```

Register with **Claude Code** (`~/.claude/.mcp.json`):
```json
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

Register with **Gemini CLI** (`~/.gemini/settings.json`):
```json
{
  "mcpServers": {
    "memory": {
      "uri": "http://127.0.0.1:8787/mcp"
    }
  }
}
```
Then run: `python -m mcp_memory --http`

## MCP Tools (14 total)

### Write — capture knowledge as it happens
| Tool | Description |
|------|-------------|
| `memory_store` | Smart store — auto-classifies type (decision/resolved/question/knowledge) |
| `memory_record_decision` | Record a decision (what, why, how) |
| `memory_record_resolved` | Record a resolved issue (what, how) |
| `memory_record_question` | Record an open question (with priority 1-3) |
| `memory_record_knowledge` | Record a knowledge item (title, content, tags) |

### Read — recall what matters
| Tool | Description |
|------|-------------|
| `memory_list` | List recent memories, filter by type |
| `memory_get` | Get specific memory by ID (searches all tables) |
| `memory_get_summary` | Quick counts: decisions, resolved, questions, knowledge |

### Delete
| Tool | Description |
|------|-------------|
| `memory_delete` | Delete a memory by ID |

### Search — find by meaning, not just keywords
| Tool | Description |
|------|-------------|
| `memory_search` | Semantic vector search across all workspaces and domains |

### Admin
| Tool | Description |
|------|-------------|
| `memory_status` | System overview: local counts, cloud status, embedding stats |
| `memory_compact` | Check session health, trigger compaction |
| `memory_oracle_summary` | Cross-workspace summary from cloud DB |

## Memory Architecture

```
Layer 1: session.md         ← ephemeral (current conversation context)
Layer 2: SQLite memory.db   ← structured (per-workspace, always local)
Layer 3: Knowledge files    ← markdown (shared via git, human-readable)
Layer 4: Cloud DB           ← unified (cross-workspace, vector search)

MCP Memory Server operates on Layer 2 + Layer 4.
Layer 1 and 3 are managed by your AI agent and git.
```

### Memory Types

| Type | When to Use | Example |
|------|-------------|---------|
| **Decision** | You chose a path | "Decided to use Clerk for auth — lower maintenance cost" |
| **Resolved** | You fixed something | "JWT race condition — fixed with mutex lock" |
| **Question** | You need an answer | "Should we add Redis? DB queries are slow" |
| **Knowledge** | You learned something | "Oracle VECTOR columns support cosine similarity" |

### Domain Isolation

Every workspace belongs to a **domain**: `work`, `personal`, or `system`.

- Write operations always go to the current workspace
- Read operations default to current workspace
- Search can span `all` domains or filter by one
- Work agents can't accidentally see personal data (and vice versa)

## Cloud Database (Optional)

The server works 100% offline with SQLite. For cross-workspace search and vector similarity, add a cloud database.

### Supported Backends

| Backend | Status | Vector Search |
|---------|--------|---------------|
| **SQLite** | Built-in (default) | Text search only |
| **Oracle AI Database** | Supported | Native `VECTOR` type + cosine similarity |
| **PostgreSQL + pgvector** | Planned | `vector` extension |
| **Supabase** | Planned | pgvector + REST API |

### Vector Search

When a cloud DB with vector support is configured:

1. Knowledge items sync from local SQLite to cloud
2. Embeddings are generated (OpenAI, local models, or DB-native)
3. `memory_search` uses cosine similarity to find semantically related memories
4. Results include source workspace and domain for context

```
You: "How did we handle auth?"
→ Finds: "Decided to use Clerk for auth" (workspace: api-backend, domain: work)
→ Finds: "JWT refresh token best practices" (workspace: knowledge-base, domain: personal)
```

## Configuration

Config lives at `~/.mcp-memory/config.json`:

```json
{
  "workspace_root": "~/Documents/Workspace",
  "workspace_map": "~/path/to/workspace-map.json",
  "cloud_db": {
    "enabled": false,
    "type": "oracle",
    "connection": "..."
  },
  "embedding": {
    "provider": "none",
    "model": "text-embedding-3-small"
  }
}
```

Run `python setup_config.py` for interactive setup.

## Transport Modes

```bash
# STDIO — for Claude Code (default)
python -m mcp_memory

# HTTP — for Gemini CLI, Codex CLI, web clients
python -m mcp_memory --http
# → http://127.0.0.1:8787/mcp
```

## Philosophy

> "The best knowledge system is one that captures everything and surfaces only what's relevant."

This isn't just a memory store. It's a **knowledge base that grows with you**:

- **Structured by default** — decisions, questions, and knowledge are different things. Treat them differently.
- **Workspace-aware** — your AI agent knows which project it's in. Memory follows.
- **Domain-isolated** — work is work, personal is personal. Cross-reference only when you choose.
- **Layered architecture** — ephemeral → structured → permanent → cloud. Each layer serves a purpose.
- **Agent-agnostic** — any MCP-compatible tool can read and write. Your memory isn't locked to one vendor.

## License

MIT
