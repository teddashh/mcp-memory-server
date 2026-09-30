# MCP Memory Server

**English** · [繁體中文](README.zh-TW.md)

An MCP server that gives AI agents typed long-term memory (decisions, resolved issues, open questions, knowledge) in one SQLite file per workspace, with salience ranking and optional Oracle-backed vector search and audit queries.

**Project page:** https://teddashh.github.io/mcp-memory-server/

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](#license)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![Tools](https://img.shields.io/badge/MCP_Tools-18-orange.svg)](#mcp-tools-18)
[![CJK Ready](https://img.shields.io/badge/CJK-Ready-red.svg)](#cjk-aware-session-check)

> **Status:** v0.1.0, published on 2026-03-31 and not actively maintained since. The tools still load on current FastMCP (checked with fastmcp 4.0.10), but the server expects databases it does not create. Read [Status and limits](#status-and-limits) before you build on it.

[Quick start](#quick-start) · [Tools](#mcp-tools-18) · [Storage](#how-memory-is-stored) · [Salience](#salience) · [CJK](#cjk-aware-session-check) · [Configuration](#configuration) · [Status](#status-and-limits)

---

## Why

AI agents are stateless. Every new session starts from zero, and the decisions, fixes, and hard-won knowledge from the last one are gone. A single notes file helps until it grows too long to load. This server stores what an agent learns as typed records, one database per workspace, and ranks recall by how often a record is actually used.

---

## Quick start

Requires Python 3.11+.

### 1. Install

```bash
git clone https://github.com/teddashh/mcp-memory-server.git
cd mcp-memory-server
pip install -e .              # or: pip install -e ".[embeddings]" for OpenAI embeddings
python setup_config.py        # optional; press Enter to keep the defaults
```

### 2. Create a workspace

The server does not create its databases. It needs a workspace map and a `memory.db` for each workspace. With the default paths:

```bash
mkdir -p ~/Documents/claude-setup ~/Documents/Workspace/my-project/.claude-memory
echo '{"my-project": "my-project"}' > ~/Documents/claude-setup/workspace-map.json
```

Save the SQL below as `schema.sql` and, from that folder, create the database (any SQLite client works too):

```bash
python - <<'PY'
import sqlite3
from pathlib import Path
ws = Path.home() / "Documents/Workspace/my-project"
db = sqlite3.connect(ws / ".claude-memory" / "memory.db")
db.executescript(Path("schema.sql").read_text())
PY
```

<details>
<summary><code>schema.sql</code>: the minimal local schema the tools expect</summary>

```sql
CREATE TABLE decisions (
  id TEXT PRIMARY KEY, date TEXT, what TEXT NOT NULL, why TEXT, how TEXT, tags TEXT,
  status TEXT, created_at TEXT DEFAULT (datetime('now')),
  access_count INTEGER DEFAULT 0, last_accessed TEXT, salience REAL DEFAULT 1.0);
CREATE TABLE resolved (
  id TEXT PRIMARY KEY, what TEXT NOT NULL, how TEXT, tags TEXT,
  date TEXT DEFAULT (date('now')), created_at TEXT DEFAULT (datetime('now')),
  access_count INTEGER DEFAULT 0, last_accessed TEXT, salience REAL DEFAULT 1.0);
CREATE TABLE open_questions (
  id TEXT PRIMARY KEY, question TEXT NOT NULL, context TEXT, tags TEXT, priority INTEGER DEFAULT 2,
  raised TEXT DEFAULT (datetime('now')), created_at TEXT DEFAULT (datetime('now')),
  access_count INTEGER DEFAULT 0, last_accessed TEXT, salience REAL DEFAULT 1.0);
CREATE TABLE knowledge_items (
  id TEXT PRIMARY KEY, title TEXT NOT NULL, content TEXT, tags TEXT,
  written_to_obsidian INTEGER DEFAULT 0, created_at TEXT DEFAULT (datetime('now')),
  access_count INTEGER DEFAULT 0, last_accessed TEXT, salience REAL DEFAULT 1.0);
CREATE TABLE daily_logs (id TEXT PRIMARY KEY);
```

The repository ships no schema or migrations; this one is derived from the queries in `mcp_memory/server.py`. `salience` needs its default of 1.0, or `memory_reinforce` fails on a new record. Nothing in the code sets `written_to_obsidian`, so `memory_list` shows knowledge items as `pending`.

</details>

### 3. Register with Claude Code

Run this inside the project that should use the workspace, with the Python you installed into:

```bash
claude mcp add memory -e MEMORY_WORKSPACE=my-project -- python -X utf8 -m mcp_memory
```

Without `MEMORY_WORKSPACE`, the server matches its working directory against the workspace map and falls back to `unknown`, which cannot store anything. `setup_config.py` ends by printing a JSON snippet for `~/.claude/.mcp.json`; current Claude Code does not document that file, so use `claude mcp add` (or a project `.mcp.json`) instead.

### 4. Check

`claude mcp list` should show `memory` as connected. Then ask the agent to call `memory_status`. On a new workspace it returns:

```text
MCP Memory Server v0.1.0
Workspace: my-project
Local: [my-project] Decisions:0 Resolved:0 Questions:0 Knowledge:0 (pending:0) DailyLogs:0
Oracle: not connected
Embeddings: none
```

### Other transports and the decay job

```bash
python -m mcp_memory            # stdio (default)
python -m mcp_memory --http     # streamable HTTP at http://127.0.0.1:8787/mcp
python -m mcp_memory --decay    # one salience decay pass over every mapped workspace
```

In HTTP mode one server process serves every client, so the workspace comes from that process's `MEMORY_WORKSPACE` or working directory. The package also installs an `mcp-memory` console script that starts the same server.

---

## MCP tools (18)

### Write

| Tool | Description |
|------|-------------|
| `memory_store` | Store with automatic type detection: decision, resolved, question, or knowledge |
| `memory_record_decision` | Record a decision: what, why, how |
| `memory_record_resolved` | Record a resolved issue: what, how |
| `memory_record_question` | Record an open question with priority 1 (high) to 3 (low) |
| `memory_record_knowledge` | Record a knowledge item: title, content |

### Read

| Tool | Description |
|------|-------------|
| `memory_list` | List recent records, optionally filtered by type |
| `memory_get` | Get one record by id (counts as an access) |
| `memory_get_summary` | Record counts for a workspace |

### Delete

| Tool | Description |
|------|-------------|
| `memory_delete` | Delete a record by id |

### Search

| Tool | Description |
|------|-------------|
| `memory_search` | Search knowledge items: vector search on Oracle when embeddings are configured, otherwise a salience-ranked text match |

### Salience

| Tool | Description |
|------|-------------|
| `memory_reinforce` | Raise a record's salience by 20% |

### Audit trail (Oracle, read-only)

| Tool | Description |
|------|-------------|
| `memory_audit_search` | Search `AUDIT_LOG` by keyword, date, sender, or importance (H/M/L) |
| `memory_audit_stats` | Counts by importance, direction, category, and suspicious flag |
| `memory_daily_report` | Read `DAILY_REPORTS`: email and calendar counts, priorities, narrative |
| `memory_activity_log` | Read `ACTIVITY_LOG`: scheduled tasks and dispatches |

### Admin

| Tool | Description |
|------|-------------|
| `memory_status` | Local counts; with Oracle, cloud counts and the last sync time; embedding provider |
| `memory_compact` | CJK-aware size check of `session.md` that recommends when to compact |
| `memory_oracle_summary` | Per-workspace record counts from Oracle |

---

## How memory is stored

```
MCP client (Claude Code over stdio, or any client over HTTP)
      │ tool call
      ▼
mcp_memory: resolve the workspace (MEMORY_WORKSPACE, else working directory + workspace-map.json)
      │
      ├── SQLite   <workspace_root>/<folder>/.claude-memory/memory.db   read and write
      │
      └── Oracle   optional                                              read only
                   vector search, audit log, daily reports, activity log
```

- **Writes** always go to the current workspace.
- **Record operations** (`list`, `get`, `get_summary`, `delete`, `reinforce`) default to the current workspace and accept a `workspace` argument for another one.
- **Search** covers every mapped workspace. On Oracle, `domain` (`work` or `personal`) narrows it through the domain column of the `WORKSPACES` table.
- A workspace named `claude-setup` is built in. Its database lives in `<claude_setup_dir>/.claude-memory/memory.db`, and it is selected when the working directory path contains `claude-setup`.

### Tables the code expects

| Store | Tables |
|-------|--------|
| SQLite, per workspace | `decisions`, `resolved`, `open_questions`, `knowledge_items`, `daily_logs` |
| Oracle, optional | `WORKSPACES`, `DECISIONS`, `RESOLVED`, `OPEN_QUESTIONS`, `KNOWLEDGE_ITEMS` (with a `VECTOR` column named `embedding`), `AUDIT_LOG`, `DAILY_REPORTS`, `ACTIVITY_LOG`, `SYNC_LOG` |

Nothing in this repository creates these tables, syncs SQLite to Oracle, writes embeddings, or fills the audit tables.

---

## Salience

Every record carries `access_count`, `last_accessed`, and `salience`, which starts at 1.0.

```
memory_get, or a hit in local search    salience × 1.05   capped at 2.0
memory_reinforce                        salience × 1.20   capped at 2.0
--decay, untouched for 30+ days         salience × 0.95   no floor
```

- Text search orders results by salience (on Oracle, then by recency). Oracle vector search orders by cosine distance only.
- Access is tracked on `memory_get` and on the local SQLite search path. The Oracle search paths do not update salience.
- Decay lowers scores and never deletes rows. It applies once per `--decay` run, so schedule it daily if you want a daily rate.

Reinforcement plus decay was inspired by the Weibull decay model in [memory-lancedb-pro](https://github.com/CortexReach/memory-lancedb-pro). This server uses plain multiplicative factors instead.

---

## CJK-aware session check

`memory_compact` estimates the token size of the workspace's `.claude-memory/session.md` by character class:

| Character class | Tokens per character |
|-----------------|----------------------|
| CJK ideographs, CJK symbols and punctuation, full-width forms | 1.5 |
| Hiragana and Katakana | 1.5 |
| Korean Hangul | 1.5 |
| Emoji (code points from U+1F600 up) | 2.0 |
| Everything else, including ASCII | 0.25 |

A flat 0.25-per-character rule would put pure CJK text at one sixth of this estimate. Computed with the server's `estimate_tokens`:

```
Text: "資料庫 schema 部署完成，所有表都已經建好了。"   (26 characters)

Flat 0.25 per character:  6.5 tokens
CJK-aware estimate:       29 tokens
```

Above 3,000 estimated tokens or 100 lines, the tool reports `COMPACT RECOMMENDED`:

```
[my-project] session.md status: COMPACT RECOMMENDED
  Lines: 142 | Chars: 5830 | Estimated tokens: 4102
  (CJK-aware: CJK=1.5tok, ASCII=0.25tok, Emoji=2.0tok)
  Threshold: 100 lines or 3000 tokens
  → Agent should: read session.md, extract items via memory_record_*, trim session.md
```

`memory_compact` only reports. Extracting records and trimming `session.md` is left to the agent.

The character-class approach comes from [lossless-claw-enhanced](https://github.com/win4r/lossless-claw-enhanced).

---

## Memory types and auto-classification

| Type | Use it when | Fields |
|------|-------------|--------|
| Decision | You chose a path | what, why, how |
| Resolved | You fixed something | what, how |
| Question | You need an answer | question, context, priority 1 to 3 |
| Knowledge | You learned something | title, content |

Every type also takes comma-separated `tags`.

With `type="auto"` (the default), `memory_store` looks for English keywords in the lower-cased text:

- `decided`, `chose`, `decision`, `will use`, `going with`: decision, split on `|` into what, why, how
- `fixed`, `solved`, `resolved`, `the fix`, `root cause`: resolved, split on `|` into what, how
- `?`, `should we`, `how to`, `what if`, `need to figure`: question
- anything else: knowledge, titled with the first 100 characters

Only English keywords and the half-width `?` count. Chinese text such as 「我們決定改用 SQLite」 or a question ending in a full-width 「？」 is stored as knowledge unless you pass `type` yourself.

---

## Oracle features

With `oracle.enabled` and a wallet connection through `python-oracledb`:

- `memory_search` runs `VECTOR_DISTANCE(..., COSINE)` over `KNOWLEDGE_ITEMS.embedding` when an OpenAI embedding provider is configured, and a salience-ranked text match otherwise.
- The four audit-trail tools query `AUDIT_LOG`, `DAILY_REPORTS`, and `ACTIVITY_LOG`. Without Oracle they return a message saying a cloud database is required.
- `memory_status` adds workspace, knowledge, embedding, audit, report, and activity counts, plus the last `SYNC_LOG` time.
- `memory_oracle_summary` lists per-workspace counts, grouped by domain.

Vector search needs an Oracle database with AI Vector Search (`VECTOR_DISTANCE`). Oracle is the only cloud backend in the code; there is no PostgreSQL, Supabase, or MySQL backend.

---

## Configuration

`~/.mcp-memory/config.json` is optional. Its values are merged over these defaults from `mcp_memory/config.py` (the `~` paths below are resolved to your home directory):

```json
{
  "workspace_root": "~/Documents/Workspace",
  "claude_setup_dir": "~/Documents/claude-setup",
  "workspace_map": "~/Documents/claude-setup/workspace-map.json",
  "knowledge_dir": "~/Documents/knowledge",
  "oracle": {
    "enabled": false,
    "wallet_dir": "",
    "wallet_password": "",
    "dsn": "",
    "user": "CLAUDE_MEMORY",
    "password": ""
  },
  "embedding": {
    "provider": "none",
    "model": "text-embedding-3-small",
    "api_key": ""
  }
}
```

- Paths you write yourself must be absolute. The code does not expand `~`.
- `workspace_map` points to a JSON object that maps a workspace id to a folder under `workspace_root`.
- `embedding.provider` is `none` or `openai`.
- `knowledge_dir` is loaded but not used by the current code.
- Environment overrides: `MEMORY_WORKSPACE` (the current workspace), `MCP_MEMORY_WORKSPACE_ROOT`, `MCP_MEMORY_ORACLE_PASSWORD`, `OPENAI_API_KEY`.
- `setup_config.py` asks for the workspace root, the `claude-setup` folder, the Oracle wallet settings, and the embedding provider, then writes the file. It stores passwords and API keys in plain text, so prefer the environment variables for secrets.

---

## Design choices

1. **Structured by default.** Decisions, fixes, questions, and knowledge have different fields, so they get different tables.
2. **Salience, not deletion.** Old records fade in ranking, but decay never removes them.
3. **CJK-aware from the start.** Size checks weight characters by class instead of assuming English.
4. **Agent-agnostic.** Any MCP client can use it; nothing is tied to one AI vendor.

---

## Status and limits

v0.1.0 was written and published on 2026-03-31. There have been no commits since, and the project is not actively maintained.

Checked on 2026-09-30 with Python 3.14 and fastmcp 4.0.10:

- All 18 tools register, and both the stdio and HTTP transports start.
- With a prepared `memory.db`, the local tools work: store, list, get, delete, reinforce, local search, summary, status, and the session check.
- `--decay` lowers salience on stale records.

Known limits:

- No schema, migrations, or tests ship with the repository.
- Oracle is the only cloud backend. Nothing here syncs SQLite to Oracle, writes embeddings, or fills the audit tables.
- `memory_search` covers knowledge items only. Reach decisions, resolved issues, and questions through `memory_list` and `memory_get`.
- Auto-classification recognizes English keywords only.
- Decay has no floor, and its pace depends on how often you run it.
- `setup_config.py` stores secrets in plain JSON and suggests an undocumented Claude Code config path.
- `pyproject.toml` requires `oracledb` even when Oracle is off, and `fastmcp>=3.0` has no upper bound.

---

## Credits

- [FastMCP](https://github.com/PrefectHQ/fastmcp): the MCP server framework
- [python-oracledb](https://github.com/oracle/python-oracledb): the Oracle driver
- [memory-lancedb-pro](https://github.com/CortexReach/memory-lancedb-pro): the idea of reinforcement plus decay
- [lossless-claw-enhanced](https://github.com/win4r/lossless-claw-enhanced): the character-class token estimate

## Contributing

Issues and pull requests are welcome.

## License

MIT, as declared by the author. A separate LICENSE file has not been added yet.
