<div align="center">

# MCP Memory Server

### Every interaction leaves a trace. Every trace becomes knowledge.
### 凡走過必留下痕跡。每個痕跡都將成為知識。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![Tools](https://img.shields.io/badge/MCP_Tools-19-orange.svg)](#mcp-tools-19--工具一覽)
[![CJK Ready](https://img.shields.io/badge/CJK-Ready-red.svg)](#cjk-aware-context-management--cjk-感知的-context-管理)

**A unified long-term memory, knowledge base, and audit trail for AI agents.**

**統一的 AI Agent 長期記憶、知識庫與稽核軌跡系統。**

[Quick Start](#quick-start--快速開始) | [Tools](#mcp-tools-19--工具一覽) | [Architecture](#architecture--系統架構) | [Salience](#salience-engine--記憶-salience-引擎) | [繁體中文](#繁體中文版)

</div>

---

## The Problem / 問題

AI agents are stateless. They forget **everything** between sessions. Your decisions, your solved problems, your hard-won knowledge — gone. Every new conversation starts from zero.

Existing memory solutions are either too simple (flat key-value stores) or too opinionated (locked to one vendor, one database, one language).

AI 代理是無狀態的。它們在對話之間會**遺忘所有事情**。現有的記憶方案不是太簡單（扁平的 key-value），就是太限制（綁定單一廠商、資料庫、語言）。

## The Solution / 解決方案

**MCP Memory Server** gives every AI agent a persistent brain with:

```
Any AI Agent ──→ MCP Tool Call ──→ Memory Server ──→ Local DB + Cloud DB
                 (native)          (auto-detect       (structured +
                                    workspace)         vector search)
```

| What makes it different | 獨特之處 |
|------------------------|---------|
| **Not just memory — a knowledge base.** Decisions, questions, and knowledge are fundamentally different things. We store them differently. | **不只是記憶——是知識庫。** 決策、問題、知識本質不同，分別儲存。 |
| **Not just storage — intelligent recall.** Salience tracking, access reinforcement, and natural decay surface what matters. | **不只是儲存——是智慧回想。** Salience 追蹤、存取強化、自然衰減，讓重要的浮上來。 |
| **Not just local — cross-workspace.** 18-table cloud schema with vector search across all your projects. | **不只是本地——跨專案。** 18 張表的雲端 schema，跨所有專案的向量搜尋。 |
| **Not just English — CJK-native.** Token estimation built for Chinese, Japanese, Korean from day one. | **不只是英文——原生 CJK。** Token 估算從第一天就為中日韓文設計。 |

---

## Quick Start / 快速開始

```bash
git clone https://github.com/teddashh/mcp-memory-server.git
cd mcp-memory-server
pip install -e .

# Interactive setup (optional — works with SQLite defaults)
python setup_config.py
```

### Claude Code
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

### Gemini CLI / Codex CLI
```bash
python -m mcp_memory --http  # → http://127.0.0.1:8787/mcp
```

---

## Architecture / 系統架構

```
┌─ Claude Code ────────────┐
├─ Gemini CLI ─────────────┤
├─ Codex CLI ──────────────┼──→  MCP Memory Server (19 tools)
├─ Custom MCP Client ──────┤          │
└─ Any Future AI Tool ─────┘          │
                                      ├── L2: SQLite (local, fast, per-workspace)
                                      │     └── Salience tracking + CJK token estimation
                                      │
                                      ├── L3: Markdown (git-synced, human-readable)
                                      │     └── Knowledge files, daily logs
                                      │
                                      └── L4: Cloud DB (cross-workspace, vector search)
                                            └── 18 tables + audit trail + daily reports
```

### The 4-Layer Memory Model / 四層記憶模型

```
L1  session.md       ← 短暫：當前對話的脈絡（每次載入，compact 控制大小）
      ↓ compact (agent-driven, CJK-aware token estimation)
L2  SQLite memory.db ← 結構化：每個專案獨立，salience 追蹤，毫秒級查詢
      ↓ sync (scheduled, incremental, idempotent)
L3  Markdown files   ← 永久：Git 同步，人類可讀，Obsidian 知識庫
L4  Cloud DB         ← 統一：跨專案向量搜尋，18 張表，完整稽核軌跡
```

| Layer | Storage | Speed | Scope | 說明 |
|-------|---------|-------|-------|------|
| **L1** | `session.md` | Instant | Current conversation | 當前對話脈絡 |
| **L2** | SQLite | ~1ms | Current workspace | 當前專案的結構化記憶 |
| **L3** | Markdown | ~10ms | Shared via git | Git 同步的知識庫 |
| **L4** | Cloud DB | ~100ms | All workspaces | 跨所有專案 + 向量搜尋 |

**Key principle: each layer only talks to its neighbor. No skipping layers.**

**核心原則：每層只與相鄰層互動，不跳層。**

```
L1 ──compact──→ L2 ──sync──→ L4
     ↑ agent        ↑ scheduler
     主動            自動 (30min)

Query: L2 (fast) → L4 (cross-workspace)
```

---

## MCP Tools (19) / 工具一覽

### Write — Capture knowledge as it happens / 寫入——即時捕捉知識

| Tool | Description | 說明 |
|------|-------------|------|
| `memory_store` | Smart store — auto-classifies type (decision/resolved/question/knowledge) | 智慧儲存——自動分類類型 |
| `memory_record_decision` | Record a decision (what, why, how) | 記錄決策（做什麼、為什麼、怎麼做） |
| `memory_record_resolved` | Record a resolved issue | 記錄已解決的問題 |
| `memory_record_question` | Record an open question (priority 1-3) | 記錄未解問題（優先級 1-3） |
| `memory_record_knowledge` | Record a knowledge item | 記錄知識項目 |

### Read — Recall what matters / 讀取——回憶重要的事

| Tool | Description | 說明 |
|------|-------------|------|
| `memory_list` | List recent memories, filter by type | 列出最近記憶，可按類型篩選 |
| `memory_get` | Get a specific memory by ID (auto-tracks access) | 依 ID 取得（自動追蹤存取） |
| `memory_get_summary` | Quick counts per workspace | 快速查看各表計數 |

### Delete / 刪除

| Tool | Description | 說明 |
|------|-------------|------|
| `memory_delete` | Delete a memory by ID | 依 ID 刪除記憶 |

### Search — Find by meaning, not keywords / 搜尋——依語意查找

| Tool | Description | 說明 |
|------|-------------|------|
| `memory_search` | Salience-weighted semantic search across all workspaces | Salience 加權的跨專案語意搜尋 |

### Salience — Important memories surface naturally / 記憶重要性——重要的自然浮上來

| Tool | Description | 說明 |
|------|-------------|------|
| `memory_reinforce` | Manually boost a memory's salience (+20%) | 手動強化記憶重要性（+20%） |

### Trail — Full audit trail / 軌跡——完整稽核

| Tool | Description | 說明 |
|------|-------------|------|
| `memory_audit_search` | Search audit trail (keyword, date, sender, importance) | 搜尋稽核軌跡 |
| `memory_audit_stats` | Audit statistics (by importance, direction, category) | 稽核統計 |
| `memory_daily_report` | Daily reports (email stats, calendar, narrative) | 每日報告 |
| `memory_activity_log` | Agent activity log (scheduled tasks, dispatches) | 代理活動日誌 |

### Admin / 管理

| Tool | Description | 說明 |
|------|-------------|------|
| `memory_status` | System overview (local + cloud + trail + embeddings) | 系統總覽 |
| `memory_compact` | CJK-aware session health check + compaction trigger | CJK 感知的 session 健康檢查 |
| `memory_oracle_summary` | Cross-workspace summary from cloud | 雲端跨專案摘要 |

---

## Salience Engine / 記憶 Salience 引擎

Not all memories are equal. Some are accessed daily, others are forgotten. The salience engine ensures **important memories surface naturally while noise fades away**.

不是所有記憶都一樣重要。有些每天被查詢，有些被遺忘。Salience 引擎確保**重要的記憶自然浮上來，噪音自然沈下去**。

Inspired by [memory-lancedb-pro](https://github.com/CortexReach/memory-lancedb-pro)'s Weibull decay model, adapted for our multi-layer architecture.

### How It Works / 運作方式

```
Memory born → salience = 1.0
     │
     ├── Accessed (memory_get / memory_search) → salience *= 1.05  (+5% per access)
     ├── Reinforced (memory_reinforce)          → salience *= 1.20  (+20% manual boost)
     │                                            cap at 2.0
     │
     └── Not accessed for 30+ days              → salience *= 0.95  (-5% daily decay)
                                                   floor at 0.01

Search results sorted by: salience DESC, then recency
```

**Every `memory_get` and `memory_search` automatically tracks access.** No manual intervention needed. Frequently used memories stay relevant. Stale memories gradually fade — but they're never deleted. They just sink lower in search results.

**每次 `memory_get` 和 `memory_search` 自動追蹤存取。** 不需手動操作。常用的記憶保持相關性。陳舊的記憶逐漸淡出——但永不刪除，只是在搜尋結果中排序靠後。

### Fields Added to Every Memory / 每筆記憶加入的欄位

| Field | Type | Description | 說明 |
|-------|------|-------------|------|
| `access_count` | Integer | Total times accessed | 總存取次數 |
| `last_accessed` | Timestamp | When last read or searched | 最後存取時間 |
| `salience` | Float (0.01–2.0) | Current importance score | 當前重要性分數 |

---

## CJK-Aware Context Management / CJK 感知的 Context 管理

Standard token estimation assumes ASCII (~0.25 tokens/char). This **underestimates CJK content by 3-6x**, causing context window overflow and premature compaction.

標準的 token 估算假設 ASCII（~0.25 tokens/字元）。這**低估 CJK 內容 3-6 倍**，導致 context window 溢出。

Inspired by [lossless-claw-enhanced](https://github.com/win4r/lossless-claw-enhanced)'s character-class approach:

| Character Class | Tokens/Char | Examples |
|----------------|-------------|----------|
| ASCII | 0.25 | `Hello world` → 3 tokens |
| **CJK** | **1.5** | `你好世界` → 6 tokens |
| Emoji | 2.0 | Emoji sequences |
| Hiragana/Katakana | 1.5 | Japanese text |
| Korean Hangul | 1.5 | Korean text |

### Impact / 影響

```
Text: "資料庫 schema 部署完成，所有表都已經建好了。"

Standard estimate:  22 chars × 0.25 = 6 tokens   ← WRONG
CJK-aware estimate: 22 chars → 28 tokens          ← CORRECT (4.7x difference)
```

`memory_compact` uses CJK-aware estimation to accurately determine when `session.md` needs compaction:

```
[workspace] session.md status: COMPACT RECOMMENDED
  Lines: 142 | Chars: 5830 | Estimated tokens: 4102
  (CJK-aware: CJK=1.5tok, ASCII=0.25tok, Emoji=2.0tok)
  Threshold: 100 lines or 3000 tokens
  → Agent should: read session.md, extract items via memory_record_*, trim session.md
```

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

`memory_store` auto-classifies: if it contains "decided/chose" → decision, "fixed/solved" → resolved, "?" → question, else → knowledge.

`memory_store` 自動分類：包含「決定/選擇」→ 決策，「修好/解決」→ 已解決，「？」→ 問題，其他 → 知識。

---

## Audit Trail / 稽核軌跡

> *"Every interaction leaves a trace."* — This is not just a tagline. It's the architecture.
>
> *「凡走過必留下痕跡。」* —— 這不只是標語，這是架構。

| Table | Scale | Purpose | 用途 |
|-------|-------|---------|------|
| **AUDIT_LOG** | Scales to 100K+ | Every email, message, and action — timestamped, categorized, suspicious-flagged | 每封郵件和動作的完整紀錄 |
| **ACTIVITY_LOG** | Grows daily | Agent scheduled task logs, dispatches, health checks | 代理排程任務、派送、健康檢查 |
| **DAILY_REPORTS** | 1 per day | Auto-generated daily summaries with email stats, calendar, narrative | 自動產生的每日摘要 |
| **AUDIT_PROGRESS** | Per source | Data source processing tracker | 資料來源處理進度 |

Search by date, sender, keyword, importance (H/M/L), suspicious flag. Get aggregate stats by period.

---

## Domain Isolation / 領域隔離

Every workspace belongs to a **domain**: `work`, `personal`, or `system`.

```
                    ┌─────── work ───────┐
                    │ project-a          │
                    │ project-b          │  ← Write isolated
                    │ report-automation  │  ← Read: current workspace default
                    └────────────────────┘
                              ↕ cross-domain search (opt-in)
                    ┌────── personal ─────┐
                    │ my-app              │  ← Separate domain
                    │ side-projects       │
                    └─────────────────────┘
```

- **Write** always goes to the current workspace / 寫入永遠寫到當前專案
- **Read** defaults to current workspace / 讀取預設只看當前專案
- **Search** can span all domains (opt-in) / 搜尋可跨領域（需明確指定）

---

## Database Schema (18 Tables) / 資料庫結構（18 張表）

<details>
<summary>Click to expand full schema / 點擊展開完整 schema</summary>

| Table | Purpose | 用途 |
|-------|---------|------|
| **WORKSPACES** | Project registry with domain tags | 專案註冊表 |
| **DECISIONS** | Decisions (what/why/how) + salience | 決策記錄 + salience |
| **RESOLVED** | Resolved issues + salience | 已解決問題 + salience |
| **OPEN_QUESTIONS** | Prioritized questions + salience | 未解問題 + salience |
| **KNOWLEDGE_ITEMS** | Knowledge + vector embeddings + salience | 知識 + 向量嵌入 + salience |
| **DAILY_LOGS** | Daily log metadata | 每日日誌 |
| **PERSONALITY_TRAITS** | Structured user understanding | 用戶特質 |
| **CROSS_REFERENCES** | Links between any records | 記錄間關聯 |
| **TAXONOMY** | Hierarchical categories | 階層分類 |
| **CONTACTS** | People and relationships | 聯絡人 |
| **SOP** | Standard operating procedures | 標準作業流程 |
| **CHANNELS** | Communication channels | 通訊管道 |
| **ACTIVITY_LOG** | Agent action trail | 代理動作軌跡 |
| **AUDIT_LOG** | Full audit trail | 完整稽核軌跡 |
| **AUDIT_PROGRESS** | Processing tracker | 處理進度 |
| **DAILY_REPORTS** | Auto-generated summaries | 每日摘要 |
| **SYNC_WATERMARK** | Incremental sync tracking | 增量同步追蹤 |
| **SYNC_LOG** | Sync history | 同步歷史 |

</details>

### Supported Cloud Backends / 支援的雲端後端

| Backend | Status | Vector Search |
|---------|--------|---------------|
| **SQLite** | Built-in (default) | Text search |
| **Oracle AI Database** | Supported | Native `VECTOR` + cosine |
| **PostgreSQL + pgvector** | Planned | `vector` extension |
| **Supabase** | Planned | pgvector + REST API |
| **MySQL / HeatWave** | Planned | ML integration |

---

## How It Compares / 與其他方案的比較

| Feature | MCP Memory Server | OpenMemory | memory-lancedb-pro |
|---------|:-:|:-:|:-:|
| Structured memory types | 4 types | key-value | 6 categories |
| Cross-workspace search | cloud DB | local only | local only |
| Vector search | Oracle / pgvector | synthetic embeddings | LanceDB |
| Salience / decay | access tracking + daily decay | no | Weibull model |
| CJK token awareness | built-in | no | no |
| Audit trail | 86K+ entries | no | no |
| Multi-agent support | Claude + Gemini + Codex | Claude + Gemini + Codex | OpenClaw only |
| Domain isolation | work / personal / system | user ID | scope-based |
| Cloud sync | scheduled incremental | no | no |
| Database choice | SQLite + any cloud DB | SQLite | LanceDB |
| 18-table schema | yes | no | no |

---

## Configuration / 設定

`~/.mcp-memory/config.json`:

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

Interactive setup: `python setup_config.py`

Transport modes:
```bash
python -m mcp_memory            # STDIO (Claude Code)
python -m mcp_memory --http     # HTTP (Gemini, Codex, web)
python -m mcp_memory --decay    # Run daily salience decay job
```

---

## Philosophy / 設計哲學

> *"The best knowledge system captures everything and surfaces only what's relevant."*
>
> *「最好的知識系統是捕捉一切，只呈現相關的。」*

1. **Structured by default** — Decisions and knowledge are different. Treat them differently.
2. **Salience, not deletion** — Old memories fade, but never disappear. They can always be found.
3. **Layers, not monoliths** — Each layer has a job. Fast local → permanent cloud. No skipping.
4. **CJK-native** — Not an afterthought. Built for multilingual from the start.
5. **Agent-agnostic** — Your memory belongs to you, not your AI vendor.
6. **Audit everything** — Every trace, every action, every day. Full accountability.

---

1. **結構化為本** —— 決策和知識本質不同，分別儲存。
2. **Salience 而非刪除** —— 舊記憶淡出，但永不消失。隨時可找回。
3. **分層而非單體** —— 每層各司其職。快速本地 → 永久雲端。不跳層。
4. **原生 CJK** —— 不是事後補丁。從第一天就為多語言設計。
5. **不綁定 AI** —— 你的記憶屬於你，不屬於 AI 廠商。
6. **稽核一切** —— 每個軌跡、每個動作、每一天。完整的可追溯性。

---

## 繁體中文版

<details>
<summary>完整繁體中文說明</summary>

### MCP Memory Server 是什麼？

一個統一的 AI 代理長期記憶系統。安裝後，你的 Claude Code、Gemini CLI、Codex CLI 都能使用 19 個 native MCP tools 來記錄和查詢記憶。

### 核心功能

- **19 個 MCP 工具**：寫入（5）、讀取（3）、刪除（1）、搜尋（1）、Salience（1）、稽核軌跡（4）、管理（3）
- **四層記憶架構**：session.md → SQLite → Markdown → Cloud DB
- **Salience 引擎**：存取追蹤 + 強化 + 自然衰減，重要的記憶自動浮上來
- **CJK 感知**：繁中/日文/韓文的 token 估算準確度提高 3-6 倍
- **領域隔離**：工作、個人、系統三個領域，寫入隔離，搜尋可跨域
- **稽核軌跡**：AUDIT_LOG + ACTIVITY_LOG + DAILY_REPORTS，完整可追溯
- **18 張表的雲端 Schema**：涵蓋記憶、知識、聯絡人、SOP、分類樹、稽核
- **離線優先**：SQLite 零配置即可運作，雲端資料庫是可選的進階功能

### 安裝

```bash
git clone https://github.com/teddashh/mcp-memory-server.git
cd mcp-memory-server && pip install -e .
python setup_config.py
```

在 `~/.claude/.mcp.json` 加入 server 設定後，重啟 Claude Code 即可使用所有 tools。

</details>

---

## Contributing / 貢獻

Issues and PRs welcome.

歡迎提交 Issue 和 Pull Request。

## License

MIT
