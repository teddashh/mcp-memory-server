<div align="center">

# MCP Memory Server

### Every interaction leaves a trace. Every trace becomes knowledge.
### 凡走過必留下痕跡。每個痕跡都將成為知識。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)

A unified long-term memory and knowledge base for AI agents.

統一的 AI Agent 長期記憶與知識庫系統。

</div>

---

```
Any AI Agent ──→ MCP Tool Call ──→ Memory Server ──→ Local DB + Cloud DB
                 (native)          (auto-detect       (structured +
                                    workspace)         vector search)
```

## Why / 為什麼需要

AI agents are stateless. They forget **everything** between sessions. Your decisions, your solved problems, your hard-won knowledge — gone. Every new conversation starts from zero.

AI 代理是無狀態的。它們在對話之間會**遺忘所有事情**。你的決定、你解過的問題、你辛苦累積的知識——全部消失。每次新對話都從零開始。

**MCP Memory Server gives every agent a brain that persists.**

**MCP Memory Server 讓每個 AI 代理都擁有持久的記憶。**

| Feature | Description |
|---------|-------------|
| **Structured Memory** | Decisions, resolved issues, questions, knowledge — each stored differently because they _are_ different. |
| **結構化記憶** | 決策、已解決問題、未解問題、知識——各自分別儲存，因為它們本質不同。 |
| **Workspace-Aware** | Auto-detects which project you're in. Memory follows context. |
| **專案感知** | 自動偵測目前所在專案。記憶跟著情境走。 |
| **Domain Isolation** | Work vs personal boundaries. Cross-reference only when you choose. |
| **領域隔離** | 工作與私人的邊界。只有你決定時才交叉查詢。 |
| **Semantic Search** | Find memories by meaning, not just keywords. Powered by vector embeddings. |
| **語意搜尋** | 用意義而非關鍵字搜尋記憶。由向量嵌入驅動。 |
| **Agent-Agnostic** | Claude, Gemini, Codex, or any MCP-compatible tool. Your memory isn't locked to one vendor. |
| **不綁定特定 AI** | Claude、Gemini、Codex 或任何 MCP 相容工具。你的記憶不被鎖在單一廠商。 |
| **Audit Trail** | Every action logged. Daily reports auto-generated. Full accountability. |
| **稽核軌跡** | 每個動作都留紀錄。每日報告自動產生。完整的可追溯性。 |
| **Offline-First** | SQLite works with zero config. Cloud DB is optional for cross-workspace power. |
| **離線優先** | SQLite 零配置即可使用。雲端資料庫是可選的進階功能。 |

---

## Architecture / 系統架構

```
┌─ Claude Code ────────────┐
├─ Gemini CLI ─────────────┤
├─ Codex CLI ──────────────┼──→  MCP Memory Server
├─ Custom MCP Client ──────┤          │
└─ Any Future AI Tool ─────┘          │
                                      ├── Layer 2: SQLite (local, fast, always available)
                                      │     └── Per-workspace isolation
                                      │
                                      ├── Layer 3: Markdown (git-synced, human-readable)
                                      │     └── Knowledge files, daily logs
                                      │
                                      └── Layer 4: Cloud DB (cross-workspace, vector search)
                                            └── Oracle / PostgreSQL / Supabase / ...
```

### The 4-Layer Memory Model / 四層記憶模型

| Layer | Storage | Purpose | 用途 |
|-------|---------|---------|------|
| **L1** | `session.md` | Ephemeral conversation context | 短暫的對話脈絡 |
| **L2** | SQLite `memory.db` | Structured per-workspace memory | 結構化的專案記憶 |
| **L3** | Markdown files | Git-synced knowledge base | Git 同步的知識庫 |
| **L4** | Cloud DB | Unified cross-workspace + vector search | 統一的跨專案搜尋 + 向量搜尋 |

> MCP Memory Server operates on **Layer 2 + Layer 4**. Layers 1 and 3 are managed by your agent and git.
>
> MCP Memory Server 負責**第 2 層和第 4 層**。第 1 層和第 3 層由你的 AI 代理和 git 管理。

---

## Quick Start / 快速開始

```bash
git clone https://github.com/teddashh/mcp-memory-server.git
cd mcp-memory-server
pip install -e .

# Interactive setup (optional — works with SQLite defaults)
python setup_config.py
```

### Register with Claude Code / 註冊到 Claude Code

Add to `~/.claude/.mcp.json`:
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

### Register with Gemini CLI

Add to `~/.gemini/settings.json`, then run `python -m mcp_memory --http`:
```json
{
  "mcpServers": {
    "memory": { "uri": "http://127.0.0.1:8787/mcp" }
  }
}
```

---

## MCP Tools (18) / 工具一覽

### Write — Capture knowledge as it happens / 寫入——即時捕捉知識

| Tool | Description | 說明 |
|------|-------------|------|
| `memory_store` | Smart store — auto-classifies type | 智慧儲存——自動分類類型 |
| `memory_record_decision` | Record a decision (what, why, how) | 記錄決策（做什麼、為什麼、怎麼做） |
| `memory_record_resolved` | Record a resolved issue | 記錄已解決的問題 |
| `memory_record_question` | Record an open question (priority 1-3) | 記錄未解問題（優先級 1-3） |
| `memory_record_knowledge` | Record a knowledge item | 記錄知識項目 |

### Read — Recall what matters / 讀取——回憶重要的事

| Tool | Description | 說明 |
|------|-------------|------|
| `memory_list` | List recent memories, filter by type | 列出最近記憶，可按類型篩選 |
| `memory_get` | Get a specific memory by ID | 依 ID 取得特定記憶 |
| `memory_get_summary` | Quick counts per workspace | 快速查看各表計數 |

### Delete / 刪除

| Tool | Description | 說明 |
|------|-------------|------|
| `memory_delete` | Delete a memory by ID | 依 ID 刪除記憶 |

### Search — Find by meaning / 搜尋——依語意查找

| Tool | Description | 說明 |
|------|-------------|------|
| `memory_search` | Semantic vector search across all workspaces | 跨所有專案的語意向量搜尋 |

### Trail — Audit logs and daily reports / 軌跡——稽核日誌與每日報告

| Tool | Description | 說明 |
|------|-------------|------|
| `memory_audit_search` | Search audit trail by keyword, date, sender, importance | 搜尋稽核軌跡（關鍵字、日期、寄件人、重要性） |
| `memory_audit_stats` | Audit statistics (by importance, direction, category) | 稽核統計（依重要性、方向、類別） |
| `memory_daily_report` | View daily reports (email counts, calendar, narrative) | 查看每日報告（郵件計數、行事曆、敘述摘要） |
| `memory_activity_log` | View agent activity (hr_patrol, pm_patrol, etc.) | 查看代理活動日誌 |

### Admin / 管理

| Tool | Description | 說明 |
|------|-------------|------|
| `memory_status` | System overview (local + cloud + trail stats) | 系統總覽（本地 + 雲端 + 軌跡統計） |
| `memory_compact` | Check session health, trigger compaction | 檢查 session 狀態，觸發壓縮 |
| `memory_oracle_summary` | Cross-workspace summary from cloud | 雲端跨專案摘要 |

---

## Memory Types / 記憶類型

| Type | When to Use | Example |
|------|-------------|---------|
| **Decision** | You chose a path | "Use Clerk for auth — lower maintenance" |
| **決策** | 做出選擇時 | 「選用 Clerk 做認證——維護成本較低」 |
| **Resolved** | You fixed something | "JWT race condition — fixed with mutex" |
| **已解決** | 修好問題時 | 「JWT race condition——用 mutex 修復」 |
| **Question** | You need an answer | "Should we add Redis?" |
| **問題** | 需要答案時 | 「要不要加 Redis？」 |
| **Knowledge** | You learned something | "VECTOR columns support cosine similarity" |
| **知識** | 學到東西時 | 「VECTOR 欄位支援 cosine similarity」 |

---

## Audit Trail / 稽核軌跡

> *"Every interaction leaves a trace."* — This is not just a tagline.

> *「凡走過必留下痕跡。」* —— 這不只是標語。

The system maintains a complete audit trail:

| Table | Purpose | 用途 |
|-------|---------|------|
| **AUDIT_LOG** | Every email, message, and action with timestamps, sender, subject, importance, and suspicious flags | 每封郵件、訊息和動作，包含時間、寄件人、主旨、重要性、可疑標記 |
| **ACTIVITY_LOG** | Agent actions (patrols, dispatches, health checks) | 代理動作（巡邏、派送、健康檢查） |
| **DAILY_REPORTS** | Auto-generated daily summaries with email stats, calendar, high-priority items, narrative | 自動產生的每日摘要：郵件統計、行事曆、高優先項目、敘述 |
| **AUDIT_PROGRESS** | Tracks which data sources have been processed | 追蹤哪些資料來源已被處理 |

**Query anything**: search by date, sender, keyword, importance level (H/M/L), or suspicious flag. Get aggregate stats by period. Review daily reports with full narrative summaries.

**查詢任何事情**：依日期、寄件人、關鍵字、重要性（高/中/低）或可疑標記搜尋。取得按期間的彙總統計。查看附有完整敘述的每日報告。

---

## Cloud Database / 雲端資料庫

The server works **100% offline** with SQLite. Cloud DB unlocks cross-workspace search and vector similarity.

伺服器可以用 SQLite **完全離線運作**。雲端資料庫解鎖跨專案搜尋和向量相似度比對。

### Supported Backends / 支援的後端

| Backend | Status | Vector Search |
|---------|--------|---------------|
| **SQLite** | Built-in | Text search |
| **Oracle AI Database** | Supported | Native `VECTOR` + cosine |
| **PostgreSQL + pgvector** | Planned | `vector` extension |
| **Supabase** | Planned | pgvector + REST API |
| **MySQL / HeatWave** | Planned | ML integration |

### How Vector Search Works / 向量搜尋原理

```
You: "How did we handle authentication?"

→ Generates embedding for your query
→ Cosine similarity search across all knowledge
→ Returns: "Decided to use Clerk for auth" (project: api-backend, domain: work)
→ Returns: "JWT refresh token best practices" (project: kb, domain: personal)
```

---

## Domain Isolation / 領域隔離

Every workspace belongs to a **domain**: `work`, `personal`, or `system`.

每個專案屬於一個**領域**：`work`（工作）、`personal`（個人）或 `system`（系統）。

- **Write** always goes to the current workspace / 寫入永遠寫到當前專案
- **Read** defaults to current workspace / 讀取預設只看當前專案
- **Search** can span all domains (opt-in) / 搜尋可跨領域（需明確指定）
- Work agents can't accidentally see personal data / 工作 AI 不會意外看到個人資料

---

## Configuration / 設定

Config file: `~/.mcp-memory/config.json`

```json
{
  "workspace_root": "~/Documents/Workspace",
  "workspace_map": "~/path/to/workspace-map.json",
  "cloud_db": {
    "enabled": false,
    "type": "oracle | postgresql | supabase",
    "connection": "..."
  },
  "embedding": {
    "provider": "none | openai | local",
    "model": "text-embedding-3-small"
  }
}
```

Interactive setup / 互動式設定: `python setup_config.py`

---

## Transport Modes / 傳輸模式

```bash
# STDIO — Claude Code (default)
python -m mcp_memory

# HTTP — Gemini CLI, Codex CLI, web clients
python -m mcp_memory --http
# → http://127.0.0.1:8787/mcp
```

---

## Philosophy / 設計哲學

> *"The best knowledge system captures everything and surfaces only what's relevant."*
>
> *「最好的知識系統是捕捉一切，只呈現相關的。」*

This isn't just a memory store. It's a **knowledge base that grows with you**.

這不只是記憶儲存。它是一個**隨你成長的知識庫**。

- **Structured by default** — Decisions and knowledge are fundamentally different. Store them differently.
- **結構化為本** —— 決策和知識本質不同。分別儲存。
- **Workspace-aware** — Context matters. Memory follows your project.
- **專案感知** —— 脈絡很重要。記憶跟著你的專案走。
- **Layered architecture** — Ephemeral → Structured → Permanent → Cloud.
- **分層架構** —— 短暫 → 結構化 → 永久 → 雲端。
- **Agent-agnostic** — Your memory belongs to you, not your AI vendor.
- **不綁定 AI** —— 你的記憶屬於你，不屬於 AI 廠商。

---

## Contributing / 貢獻

Issues and PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

歡迎提交 Issue 和 Pull Request。

## License

MIT
