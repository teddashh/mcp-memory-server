# MCP Memory Server

[English](README.md) · **繁體中文**

替 AI agent 提供分類型長期記憶的 MCP 伺服器：決策、已解決的問題、待解問題與知識，依工作區各存成一個 SQLite 檔，依重要度（salience）排序，也可以選擇接上 Oracle 做向量搜尋與稽核查詢。

**專案介紹頁：** https://teddashh.github.io/mcp-memory-server/?lang=zh-TW

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](#授權)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![Tools](https://img.shields.io/badge/MCP_Tools-18-orange.svg)](#mcp-工具18-個)
[![CJK Ready](https://img.shields.io/badge/CJK-Ready-red.svg)](#cjk-感知的-session-檢查)

> **現況：** v0.1.0，2026-03-31 發布，之後沒有持續維護。工具在目前的 FastMCP 上仍能載入（以 fastmcp 4.0.10 確認），但伺服器不會自己建立需要的資料庫。打算拿來用之前，請先看[現況與限制](#現況與限制)。

[快速開始](#快速開始) · [工具](#mcp-工具18-個) · [儲存方式](#記憶怎麼存) · [重要度](#重要度salience) · [CJK](#cjk-感知的-session-檢查) · [設定](#設定) · [現況](#現況與限制)

---

## 為什麼

AI agent 沒有狀態。每開一個新 session 都從零開始，上一次做的決策、修好的問題、好不容易學到的知識全都不見了。把東西寫進一份筆記檔可以撐一陣子，直到它長到載入不了為止。這個伺服器把 agent 學到的東西存成分類好的紀錄，每個工作區一個資料庫，再依紀錄實際被用到的頻率排序。

---

## 快速開始

需要 Python 3.11 以上。

### 1. 安裝

```bash
git clone https://github.com/teddashh/mcp-memory-server.git
cd mcp-memory-server
pip install -e .              # 要用 OpenAI embedding 就改成：pip install -e ".[embeddings]"
python setup_config.py        # 選擇性；直接按 Enter 會保留預設值
```

### 2. 建立工作區

伺服器不會自己建資料庫。它需要一份工作區對應檔，以及每個工作區各一個 `memory.db`。使用預設路徑的話：

```bash
mkdir -p ~/Documents/claude-setup ~/Documents/Workspace/my-project/.claude-memory
echo '{"my-project": "my-project"}' > ~/Documents/claude-setup/workspace-map.json
```

把下面的 SQL 存成 `schema.sql`，在同一個資料夾執行下面的指令建立資料庫（用任何 SQLite 工具也可以）：

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
<summary><code>schema.sql</code>：工具需要的最小本地 schema</summary>

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

repo 本身沒有附 schema 或 migration，這份是從 `mcp_memory/server.py` 的查詢整理出來的。`salience` 一定要有預設值 1.0，否則對新紀錄執行 `memory_reinforce` 會出錯。程式裡沒有任何地方會設定 `written_to_obsidian`，所以 `memory_list` 會把知識項目顯示為 `pending`。

</details>

### 3. 在 Claude Code 註冊

在要使用這個工作區的專案裡，用你安裝套件時的那個 Python 執行：

```bash
claude mcp add memory -e MEMORY_WORKSPACE=my-project -- python -X utf8 -m mcp_memory
```

沒有設定 `MEMORY_WORKSPACE` 時，伺服器會拿自己的工作目錄去比對工作區對應檔，比對不到就當成 `unknown`，而 `unknown` 什麼都存不進去。`setup_config.py` 最後會印出一段寫進 `~/.claude/.mcp.json` 的 JSON，但目前的 Claude Code 文件裡沒有這個檔案，請改用 `claude mcp add`（或專案裡的 `.mcp.json`）。

### 4. 確認

`claude mcp list` 應該會顯示 `memory` 已連線（Connected）。接著請 agent 呼叫 `memory_status`，新建立的工作區會回傳：

```text
MCP Memory Server v0.1.0
Workspace: my-project
Local: [my-project] Decisions:0 Resolved:0 Questions:0 Knowledge:0 (pending:0) DailyLogs:0
Oracle: not connected
Embeddings: none
```

### 其他傳輸方式與衰減排程

```bash
python -m mcp_memory            # stdio（預設）
python -m mcp_memory --http     # streamable HTTP，位址 http://127.0.0.1:8787/mcp
python -m mcp_memory --decay    # 對所有已對應的工作區做一次重要度衰減
```

HTTP 模式下，所有用戶端共用同一個伺服器程序，所以工作區取決於這個程序的 `MEMORY_WORKSPACE` 或工作目錄。套件安裝後也會有一個 `mcp-memory` 指令，啟動的是同一個伺服器。

---

## MCP 工具（18 個）

### 寫入

| 工具 | 說明 |
|------|------|
| `memory_store` | 儲存並自動判斷類型：決策、已解決、問題或知識 |
| `memory_record_decision` | 記錄決策：做什麼、為什麼、怎麼做 |
| `memory_record_resolved` | 記錄已解決的問題：問題、解法 |
| `memory_record_question` | 記錄待解問題，優先度 1（高）到 3（低） |
| `memory_record_knowledge` | 記錄知識項目：標題、內容 |

### 讀取

| 工具 | 說明 |
|------|------|
| `memory_list` | 列出最近的紀錄，可依類型篩選 |
| `memory_get` | 依 ID 取得一筆紀錄（算一次存取） |
| `memory_get_summary` | 工作區內各類紀錄的數量 |

### 刪除

| 工具 | 說明 |
|------|------|
| `memory_delete` | 依 ID 刪除一筆紀錄 |

### 搜尋

| 工具 | 說明 |
|------|------|
| `memory_search` | 搜尋知識項目：有設定 embedding 時在 Oracle 上做向量搜尋，否則用依重要度排序的文字比對 |

### 重要度

| 工具 | 說明 |
|------|------|
| `memory_reinforce` | 把一筆紀錄的重要度提高 20% |

### 稽核軌跡（Oracle，唯讀）

| 工具 | 說明 |
|------|------|
| `memory_audit_search` | 依關鍵字、日期、寄件者或重要性（H/M/L）搜尋 `AUDIT_LOG` |
| `memory_audit_stats` | 依重要性、方向、分類與可疑標記做統計 |
| `memory_daily_report` | 讀取 `DAILY_REPORTS`：郵件與行事曆數量、優先等級、摘要 |
| `memory_activity_log` | 讀取 `ACTIVITY_LOG`：排程工作與派送紀錄 |

### 管理

| 工具 | 說明 |
|------|------|
| `memory_status` | 本地數量；有 Oracle 時加上雲端數量與最後同步時間；embedding 設定 |
| `memory_compact` | 以 CJK 感知的方式檢查 `session.md` 大小，提醒何時該壓縮 |
| `memory_oracle_summary` | 從 Oracle 列出各工作區的紀錄數量 |

---

## 記憶怎麼存

```
MCP 用戶端（Claude Code 走 stdio，或任何走 HTTP 的用戶端）
      │ 工具呼叫
      ▼
mcp_memory：判斷工作區（先看 MEMORY_WORKSPACE，否則用工作目錄比對 workspace-map.json）
      │
      ├── SQLite：<workspace_root>/<資料夾>/.claude-memory/memory.db，可讀寫
      │
      └── Oracle：選配，唯讀
                  向量搜尋、稽核紀錄、每日報告、活動紀錄
```

- **寫入**一律寫到目前的工作區。
- **單筆紀錄操作**（`list`、`get`、`get_summary`、`delete`、`reinforce`）預設作用在目前的工作區，也可以用 `workspace` 參數指定其他工作區。
- **搜尋**涵蓋所有已對應的工作區。在 Oracle 上可以用 `domain`（`work` 或 `personal`）縮小範圍，依據是 `WORKSPACES` 表的 domain 欄位。
- 內建一個名為 `claude-setup` 的工作區。它的資料庫在 `<claude_setup_dir>/.claude-memory/memory.db`，當工作目錄路徑包含 `claude-setup` 時就會選用它。

### 程式預期的資料表

| 儲存位置 | 資料表 |
|----------|--------|
| SQLite，每個工作區一份 | `decisions`、`resolved`、`open_questions`、`knowledge_items`、`daily_logs` |
| Oracle，選配 | `WORKSPACES`、`DECISIONS`、`RESOLVED`、`OPEN_QUESTIONS`、`KNOWLEDGE_ITEMS`（含名為 `embedding` 的 `VECTOR` 欄位）、`AUDIT_LOG`、`DAILY_REPORTS`、`ACTIVITY_LOG`、`SYNC_LOG` |

這個 repo 裡沒有任何程式會建立這些表、把 SQLite 同步到 Oracle、寫入 embedding，或填入稽核相關的表。

---

## 重要度（salience）

每筆紀錄都有 `access_count`、`last_accessed` 與 `salience` 三個欄位，`salience` 從 1.0 開始。

```
memory_get，或本地搜尋命中          salience × 1.05   上限 2.0
memory_reinforce                    salience × 1.20   上限 2.0
--decay，超過 30 天沒被碰過         salience × 0.95   沒有下限
```

- 文字搜尋依重要度排序（在 Oracle 上再依時間新舊）。Oracle 向量搜尋只看 cosine 距離。
- 只有 `memory_get` 與本地 SQLite 搜尋會記錄存取，Oracle 的搜尋路徑不會更新重要度。
- 衰減只降分數，不刪資料列。每執行一次 `--decay` 就套用一次，想要每天衰減一次，就每天排程執行一次。

「強化加衰減」的想法來自 [memory-lancedb-pro](https://github.com/CortexReach/memory-lancedb-pro) 的 Weibull 衰減模型，這個伺服器改用單純的乘法係數。

---

## CJK 感知的 session 檢查

`memory_compact` 依字元類別估算工作區 `.claude-memory/session.md` 的 token 數：

| 字元類別 | 每字 token 數 |
|----------|---------------|
| CJK 漢字、CJK 符號與標點、全形字元 | 1.5 |
| 平假名與片假名 | 1.5 |
| 韓文 | 1.5 |
| Emoji（U+1F600 以後的碼位） | 2.0 |
| 其他字元，包括 ASCII | 0.25 |

如果一律用每字 0.25 來算，純 CJK 文字只會被估成這個數字的六分之一。用伺服器本身的 `estimate_tokens` 計算：

```
文字：「資料庫 schema 部署完成，所有表都已經建好了。」（26 個字元）

一律每字 0.25：  6.5 token
CJK 感知估算：   29 token
```

估計超過 3,000 token 或 100 行時，工具會回報 `COMPACT RECOMMENDED`：

```
[my-project] session.md status: COMPACT RECOMMENDED
  Lines: 142 | Chars: 5830 | Estimated tokens: 4102
  (CJK-aware: CJK=1.5tok, ASCII=0.25tok, Emoji=2.0tok)
  Threshold: 100 lines or 3000 tokens
  → Agent should: read session.md, extract items via memory_record_*, trim session.md
```

`memory_compact` 只負責回報，把內容整理成紀錄、精簡 `session.md` 的工作交給 agent。

依字元類別估算的做法來自 [lossless-claw-enhanced](https://github.com/win4r/lossless-claw-enhanced)。

---

## 記憶類型與自動分類

| 類型 | 什麼時候用 | 欄位 |
|------|------------|------|
| 決策 | 做了選擇 | 做什麼、為什麼、怎麼做 |
| 已解決 | 修好了問題 | 問題、解法 |
| 問題 | 需要答案 | 問題、背景、優先度 1 到 3 |
| 知識 | 學到新東西 | 標題、內容 |

每種類型都可以加上以逗號分隔的 `tags`。

`memory_store` 在 `type="auto"`（預設）時，會在轉成小寫的內容裡找英文關鍵字：

- `decided`、`chose`、`decision`、`will use`、`going with`：決策，依 `|` 拆成做什麼、為什麼、怎麼做
- `fixed`、`solved`、`resolved`、`the fix`、`root cause`：已解決，依 `|` 拆成問題、解法
- `?`、`should we`、`how to`、`what if`、`need to figure`：問題
- 其他：知識，標題取前 100 個字元

只認英文關鍵字與半形 `?`。像「我們決定改用 SQLite」這樣的中文，或以全形「？」結尾的問題，都會被存成知識，除非你自己指定 `type`。

---

## Oracle 功能

啟用 `oracle.enabled`，並透過 `python-oracledb` 以 wallet 連線之後：

- 有設定 OpenAI embedding 時，`memory_search` 會對 `KNOWLEDGE_ITEMS.embedding` 執行 `VECTOR_DISTANCE(..., COSINE)`，沒有的話改用依重要度排序的文字比對。
- 四個稽核軌跡工具會查詢 `AUDIT_LOG`、`DAILY_REPORTS` 與 `ACTIVITY_LOG`。沒有 Oracle 時，它們只會回覆需要雲端資料庫。
- `memory_status` 會多出工作區、知識、embedding、稽核、報告與活動紀錄的數量，以及 `SYNC_LOG` 的最後時間。
- `memory_oracle_summary` 依 domain 分組，列出各工作區的數量。

向量搜尋需要支援 AI Vector Search（`VECTOR_DISTANCE`）的 Oracle 資料庫。程式裡唯一的雲端後端就是 Oracle，沒有 PostgreSQL、Supabase 或 MySQL 的實作。

---

## 設定

`~/.mcp-memory/config.json` 可有可無，裡面的值會覆蓋 `mcp_memory/config.py` 的預設值（下面的 `~` 路徑在預設值裡會解析成你的家目錄）：

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

- 自己填寫的路徑必須是絕對路徑，程式不會展開 `~`。
- `workspace_map` 指向一個 JSON 物件，把工作區 ID 對應到 `workspace_root` 底下的資料夾。
- `embedding.provider` 可以是 `none` 或 `openai`。
- `knowledge_dir` 會被讀進設定，但目前的程式沒有用到。
- 可以用環境變數覆蓋：`MEMORY_WORKSPACE`（目前的工作區）、`MCP_MEMORY_WORKSPACE_ROOT`、`MCP_MEMORY_ORACLE_PASSWORD`、`OPENAI_API_KEY`。
- `setup_config.py` 會依序詢問工作區根目錄、`claude-setup` 資料夾、Oracle wallet 設定與 embedding 供應商，然後寫入設定檔。密碼與 API 金鑰會以明文儲存，機密資訊建議改用環境變數。

---

## 設計取捨

1. **預設就有結構。** 決策、修正、問題與知識的欄位不同，所以分開存在不同的表。
2. **淡出，而不是刪除。** 舊紀錄的排名會往下掉，但衰減永遠不會把它刪掉。
3. **一開始就考慮 CJK。** 檢查大小時依字元類別加權，不假設內容都是英文。
4. **不綁定 agent。** 任何 MCP 用戶端都能用，不依附在任何一家 AI 廠商身上。

---

## 現況與限制

v0.1.0 在 2026-03-31 寫完並發布，之後沒有新的 commit，目前沒有持續維護。

2026-09-30 以 Python 3.14 與 fastmcp 4.0.10 確認：

- 18 個工具都能註冊，stdio 與 HTTP 兩種傳輸方式都能啟動。
- `memory.db` 準備好之後，本地工具都能用：儲存、列出、取回、刪除、強化、本地搜尋、數量統計、狀態與 session 檢查。
- `--decay` 會調降久未使用紀錄的重要度。

已知限制：

- repo 裡沒有 schema、migration，也沒有測試。
- 雲端後端只有 Oracle。這裡沒有任何程式會把 SQLite 同步到 Oracle、寫入 embedding，或填入稽核相關的表。
- `memory_search` 只搜尋知識項目。決策、已解決的問題與待解問題，要透過 `memory_list` 與 `memory_get` 取得。
- 自動分類只認英文關鍵字。
- 衰減沒有下限，速度取決於你多久執行一次。
- `setup_config.py` 把機密資訊存成明文 JSON，建議的 Claude Code 設定路徑也不在官方文件裡。
- `pyproject.toml` 即使不用 Oracle 也會安裝 `oracledb`，而且 `fastmcp>=3.0` 沒有設定版本上限。

---

## 致謝

- [FastMCP](https://github.com/PrefectHQ/fastmcp)：MCP 伺服器框架
- [python-oracledb](https://github.com/oracle/python-oracledb)：Oracle 驅動程式
- [memory-lancedb-pro](https://github.com/CortexReach/memory-lancedb-pro)：「強化加衰減」的想法
- [lossless-claw-enhanced](https://github.com/win4r/lossless-claw-enhanced)：依字元類別估算 token 的做法

## 貢獻

歡迎提交 Issue 與 Pull Request。

## 授權

MIT，由作者聲明。repo 裡還沒有獨立的 LICENSE 檔。
