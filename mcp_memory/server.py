"""
MCP Memory Server — unified memory interface for AI agents.

Tools (18 + 1):
  Write:    memory_store, memory_record_decision, memory_record_resolved,
            memory_record_question, memory_record_knowledge
  Read:     memory_list, memory_get, memory_get_summary
  Delete:   memory_delete
  Search:   memory_search (vector + text, salience-weighted)
  Salience: memory_reinforce (boost important memories)
  Trail:    memory_audit_search, memory_audit_stats, memory_daily_report,
            memory_activity_log
  Admin:    memory_compact, memory_status, memory_oracle_summary

Usage:
  python -m mcp_memory.server          # stdio (Claude Code)
  python -m mcp_memory.server --http   # HTTP (Gemini/Codex)
"""
import json
import sys
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP

from .db import detect_workspace, get_sqlite, get_oracle, new_id, tags_to_json

mcp = FastMCP(
    "Claude Memory",
    instructions=(
        "Unified memory system for all workspaces. "
        "Use memory_store for quick saves (auto-classifies type). "
        "Use memory_search for semantic search across all knowledge. "
        "Use memory_list to see recent items. "
        "Use memory_status for system overview."
    ),
)


# ============================================================
# WRITE TOOLS
# ============================================================

@mcp.tool()
def memory_store(content: str, type: str = "auto", tags: str = "", priority: int = 2) -> str:
    """Store a memory. Type: 'decision', 'resolved', 'question', 'knowledge', or 'auto' (auto-detect).
    For decisions: content = 'what | why | how'. For questions: priority 1=high, 2=medium, 3=low."""
    if type == "auto":
        cl = content.lower()
        if any(w in cl for w in ["decided", "chose", "decision", "will use", "going with"]):
            type = "decision"
        elif any(w in cl for w in ["fixed", "solved", "resolved", "the fix", "root cause"]):
            type = "resolved"
        elif any(w in cl for w in ["?", "should we", "how to", "what if", "need to figure"]):
            type = "question"
        else:
            type = "knowledge"

    if type == "decision":
        parts = [p.strip() for p in content.split("|")]
        what = parts[0]
        why = parts[1] if len(parts) > 1 else ""
        how = parts[2] if len(parts) > 2 else ""
        return memory_record_decision(what=what, why=why, how=how, tags=tags)
    elif type == "resolved":
        parts = [p.strip() for p in content.split("|")]
        what = parts[0]
        how = parts[1] if len(parts) > 1 else ""
        return memory_record_resolved(what=what, how=how, tags=tags)
    elif type == "question":
        return memory_record_question(question=content, tags=tags, priority=priority)
    else:
        return memory_record_knowledge(title=content[:100], content=content, tags=tags)


@mcp.tool()
def memory_record_decision(what: str, why: str = "", how: str = "", tags: str = "") -> str:
    """Record a decision made in this workspace."""
    conn = get_sqlite()
    rid = new_id()
    conn.execute(
        "INSERT INTO decisions (id, date, what, why, how, tags) VALUES (?, date('now'), ?, ?, ?, ?)",
        (rid, what, why, how, tags_to_json(tags)),
    )
    conn.commit()
    conn.close()
    return f"Decision recorded [{detect_workspace()}]: {what[:60]} (id: {rid})"


@mcp.tool()
def memory_record_resolved(what: str, how: str = "", tags: str = "") -> str:
    """Record a resolved issue or problem."""
    conn = get_sqlite()
    rid = new_id()
    conn.execute(
        "INSERT INTO resolved (id, what, how, tags) VALUES (?, ?, ?, ?)",
        (rid, what, how, tags_to_json(tags)),
    )
    conn.commit()
    conn.close()
    return f"Resolved recorded [{detect_workspace()}]: {what[:60]} (id: {rid})"


@mcp.tool()
def memory_record_question(question: str, context: str = "", tags: str = "", priority: int = 2) -> str:
    """Record an open question. Priority: 1=high, 2=medium, 3=low."""
    conn = get_sqlite()
    rid = new_id()
    conn.execute(
        "INSERT INTO open_questions (id, question, context, tags, priority) VALUES (?, ?, ?, ?, ?)",
        (rid, question, context, tags_to_json(tags), priority),
    )
    conn.commit()
    conn.close()
    return f"Question recorded [{detect_workspace()}] P{priority}: {question[:60]} (id: {rid})"


@mcp.tool()
def memory_record_knowledge(title: str, content: str = "", tags: str = "") -> str:
    """Record a knowledge item. Will sync to Obsidian and Oracle."""
    conn = get_sqlite()
    rid = new_id()
    conn.execute(
        "INSERT INTO knowledge_items (id, title, content, tags, written_to_obsidian) VALUES (?, ?, ?, ?, 0)",
        (rid, title, content, tags_to_json(tags)),
    )
    conn.commit()
    conn.close()
    return f"Knowledge recorded [{detect_workspace()}]: {title[:60]} (id: {rid})"


# ============================================================
# READ TOOLS
# ============================================================

@mcp.tool()
def memory_list(type: str = "all", workspace: str = "current", limit: int = 20) -> str:
    """List recent memories. Type: 'all', 'decisions', 'resolved', 'questions', 'knowledge'."""
    ws = detect_workspace() if workspace == "current" else workspace
    conn = get_sqlite(ws)
    results = []

    tables = {
        "decisions": ("id, date, what, tags, status", "created_at"),
        "resolved": ("id, what, how, tags, date", "date"),
        "open_questions": ("id, question, priority, tags, raised", "raised"),
        "knowledge_items": ("id, title, tags, written_to_obsidian, created_at", "created_at"),
    }

    if type in ("all", "decisions"):
        rows = conn.execute(f"SELECT {tables['decisions'][0]} FROM decisions ORDER BY {tables['decisions'][1]} DESC LIMIT ?", (limit,)).fetchall()
        for r in rows:
            results.append(f"  [DEC] {r['id']} | {r['date']} | {r['what'][:70]} | {r['tags']}")

    if type in ("all", "resolved"):
        rows = conn.execute(f"SELECT {tables['resolved'][0]} FROM resolved ORDER BY {tables['resolved'][1]} DESC LIMIT ?", (limit,)).fetchall()
        for r in rows:
            results.append(f"  [RES] {r['id']} | {r['date']} | {r['what'][:70]}")

    if type in ("all", "questions"):
        rows = conn.execute(f"SELECT {tables['open_questions'][0]} FROM open_questions ORDER BY priority, {tables['open_questions'][1]} DESC LIMIT ?", (limit,)).fetchall()
        for r in rows:
            results.append(f"  [Q:P{r['priority']}] {r['id']} | {r['question'][:70]} | {r['raised']}")

    if type in ("all", "knowledge"):
        rows = conn.execute(f"SELECT {tables['knowledge_items'][0]} FROM knowledge_items ORDER BY {tables['knowledge_items'][1]} DESC LIMIT ?", (limit,)).fetchall()
        for r in rows:
            s = "synced" if r['written_to_obsidian'] else "pending"
            results.append(f"  [KNO] {r['id']} | {r['title'][:60]} | {s} | {r['created_at']}")

    conn.close()
    if not results:
        return f"No memories found in [{ws}]"
    return f"[{ws}] {len(results)} memories:\n" + "\n".join(results)


@mcp.tool()
def memory_get(id: str, workspace: str = "current") -> str:
    """Get a specific memory by ID. Searches all tables. Auto-tracks access."""
    ws = detect_workspace() if workspace == "current" else workspace
    conn = get_sqlite(ws)

    for table in ["decisions", "resolved", "open_questions", "knowledge_items"]:
        row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (id,)).fetchone()
        if row:
            _touch_access(conn, table, id)
            conn.commit()
            conn.close()
            return f"[{ws}/{table}] " + json.dumps(dict(row), ensure_ascii=False, default=str)

    conn.close()
    return f"Memory '{id}' not found in [{ws}]"


@mcp.tool()
def memory_get_summary(workspace: str = "current") -> str:
    """Get memory summary (counts) for a workspace."""
    ws = detect_workspace() if workspace == "current" else workspace
    conn = get_sqlite(ws)
    try:
        d = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        r = conn.execute("SELECT COUNT(*) FROM resolved").fetchone()[0]
        q = conn.execute("SELECT COUNT(*) FROM open_questions").fetchone()[0]
        k = conn.execute("SELECT COUNT(*) FROM knowledge_items").fetchone()[0]
        kp = conn.execute("SELECT COUNT(*) FROM knowledge_items WHERE written_to_obsidian=0").fetchone()[0]
        dl = conn.execute("SELECT COUNT(*) FROM daily_logs").fetchone()[0]
    except Exception as e:
        return f"Error [{ws}]: {e}"
    finally:
        conn.close()
    return (f"[{ws}] Decisions:{d} Resolved:{r} Questions:{q} "
            f"Knowledge:{k} (pending:{kp}) DailyLogs:{dl}")


# ============================================================
# DELETE TOOL
# ============================================================

@mcp.tool()
def memory_delete(id: str, workspace: str = "current") -> str:
    """Delete a memory by ID. Searches all tables."""
    ws = detect_workspace() if workspace == "current" else workspace
    conn = get_sqlite(ws)
    for table in ["decisions", "resolved", "open_questions", "knowledge_items"]:
        cur = conn.execute(f"DELETE FROM {table} WHERE id = ?", (id,))
        if cur.rowcount > 0:
            conn.commit()
            conn.close()
            return f"Deleted '{id}' from {table} [{ws}]"
    conn.close()
    return f"Memory '{id}' not found in [{ws}]"


# ============================================================
# SALIENCE — access tracking, reinforcement, decay
# ============================================================

def _touch_access(conn, table: str, record_id: str):
    """Increment access_count and update last_accessed for a record."""
    try:
        conn.execute(f"""
            UPDATE {table} SET
                access_count = COALESCE(access_count, 0) + 1,
                last_accessed = datetime('now'),
                salience = MIN(COALESCE(salience, 1.0) * 1.05, 2.0)
            WHERE id = ?
        """, (record_id,))
    except Exception:
        pass  # columns may not exist in old DBs


@mcp.tool()
def memory_reinforce(id: str, workspace: str = "current") -> str:
    """Manually boost a memory's salience. Use when a memory proves especially valuable."""
    ws = detect_workspace() if workspace == "current" else workspace
    conn = get_sqlite(ws)
    for table in ["decisions", "resolved", "open_questions", "knowledge_items"]:
        row = conn.execute(f"SELECT id, salience, access_count FROM {table} WHERE id = ?", (id,)).fetchone()
        if row:
            new_salience = min((row["salience"] or 1.0) * 1.2, 2.0)
            conn.execute(f"""
                UPDATE {table} SET
                    salience = ?, access_count = COALESCE(access_count, 0) + 1,
                    last_accessed = datetime('now')
                WHERE id = ?
            """, (new_salience, id))
            conn.commit()
            conn.close()
            return f"Reinforced '{id}' in {table} [{ws}]: salience {row['salience']:.2f} → {new_salience:.2f}"
    conn.close()
    return f"Memory '{id}' not found in [{ws}]"


def run_decay(workspace_id: str = None, decay_factor: float = 0.95, stale_days: int = 30):
    """Run salience decay on memories not accessed in stale_days. Called by sync-all.ps1."""
    ws = workspace_id or detect_workspace()
    conn = get_sqlite(ws)
    total = 0
    for table in ["decisions", "resolved", "open_questions", "knowledge_items"]:
        try:
            cur = conn.execute(f"""
                UPDATE {table} SET salience = COALESCE(salience, 1.0) * ?
                WHERE (last_accessed IS NULL AND created_at < datetime('now', '-{stale_days} days'))
                   OR (last_accessed < datetime('now', '-{stale_days} days'))
            """, (decay_factor,))
            total += cur.rowcount
        except Exception:
            pass
    conn.commit()
    conn.close()
    return total


# ============================================================
# SEARCH TOOLS — Oracle vector + text
# ============================================================

@mcp.tool()
def memory_search(query: str, domain: str = "all", limit: int = 10) -> str:
    """Semantic search across ALL workspaces via Oracle.
    domain: 'all', 'work', or 'personal'. Falls back to text search if vector not available."""
    oracle = get_oracle()
    if oracle is None:
        return _local_text_search(query, limit)

    cur = oracle.cursor()

    # Try vector search first
    embedding = _get_embedding(query)
    if embedding:
        return _vector_search(cur, embedding, domain, limit, oracle)

    # Fall back to text search on Oracle (salience-weighted)
    sql = """
        SELECT k.id, k.title, k.tags, w.workspace_id, w.domain,
               COALESCE(k.salience, 1.0) as sal
        FROM KNOWLEDGE_ITEMS k
        JOIN WORKSPACES w ON k.workspace_id = w.workspace_id
        WHERE LOWER(k.title) LIKE :q OR LOWER(k.tags) LIKE :q OR LOWER(k.content) LIKE :q
    """
    params = {"q": f"%{query.lower()}%"}
    if domain != "all":
        sql += " AND w.domain = :domain"
        params["domain"] = domain
    sql += " ORDER BY sal DESC, k.created_at DESC FETCH FIRST :lim ROWS ONLY"
    params["lim"] = limit

    cur.execute(sql, params)
    rows = cur.fetchall()
    if not rows:
        return f"No results for '{query}'"
    lines = [f"Search '{query}' ({len(rows)} results, salience-weighted):"]
    for r in rows:
        lines.append(f"  [{r[3]}|{r[4]}] {r[1][:55]} | sal={r[5]:.2f} | tags={r[2]}")
    return "\n".join(lines)


def _vector_search(cur, embedding, domain, limit, conn):
    """Execute vector similarity search on Oracle."""
    import array
    vec = array.array('d', embedding)

    sql = """
        SELECT k.id, k.title, k.tags, w.workspace_id, w.domain,
               VECTOR_DISTANCE(k.embedding, :qvec, COSINE) AS distance
        FROM KNOWLEDGE_ITEMS k
        JOIN WORKSPACES w ON k.workspace_id = w.workspace_id
        WHERE k.embedding IS NOT NULL
    """
    params = {"qvec": vec}
    if domain != "all":
        sql += " AND w.domain = :domain"
        params["domain"] = domain
    sql += " ORDER BY distance FETCH FIRST :lim ROWS ONLY"
    params["lim"] = limit

    try:
        cur.execute(sql, params)
        rows = cur.fetchall()
        if not rows:
            return "No vector search results (no embeddings yet?)"
        lines = [f"Vector search ({len(rows)} results, cosine distance):"]
        for r in rows:
            lines.append(f"  [{r[3]}|{r[4]}] {r[1][:50]} | dist={r[5]:.4f} | tags={r[2]}")
        return "\n".join(lines)
    except Exception as e:
        return f"Vector search error: {e}"


def _get_embedding(text: str):
    """Generate embedding via configured provider. Returns list of floats or None."""
    from .config import load_config
    config = load_config()
    provider = config["embedding"]["provider"]

    if provider == "openai" and config["embedding"]["api_key"]:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=config["embedding"]["api_key"])
            resp = client.embeddings.create(
                model=config["embedding"]["model"],
                input=text,
            )
            return resp.data[0].embedding
        except Exception:
            return None

    return None


def _local_text_search(query: str, limit: int) -> str:
    """Fallback: search local SQLite when Oracle is unavailable."""
    from .config import load_config
    config = load_config()
    results = []

    try:
        with open(config["workspace_map"]) as f:
            ws_map = json.load(f)
    except FileNotFoundError:
        return "No workspace map found"

    for ws_id in list(ws_map.keys()) + ["claude-setup"]:
        try:
            conn = get_sqlite(ws_id)
            rows = conn.execute(
                """SELECT id, title, tags, COALESCE(salience, 1.0) as sal
                   FROM knowledge_items
                   WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ?
                   ORDER BY sal DESC LIMIT ?""",
                (f"%{query.lower()}%", f"%{query.lower()}%", limit),
            ).fetchall()
            for r in rows:
                # Touch access for search hits
                _touch_access(conn, "knowledge_items", r["id"])
                results.append((r["sal"], f"  [{ws_id}] {r['id']} | {r['title'][:60]} | sal={r['sal']:.2f} | {r['tags']}"))
            conn.commit()
            conn.close()
        except Exception:
            continue

    if not results:
        return f"No local results for '{query}'"
    results.sort(key=lambda x: x[0], reverse=True)  # sort by salience
    return f"Local search '{query}' ({len(results)} results, sorted by salience):\n" + "\n".join(r[1] for r in results[:limit])


# ============================================================
# TRAIL / AUDIT TOOLS — action logs, audit trail, daily reports
# ============================================================

@mcp.tool()
def memory_audit_search(
    query: str = "", date: str = "", sender: str = "",
    importance: str = "", workspace: str = "all", limit: int = 20
) -> str:
    """Search the audit trail log. Filter by keyword, date (YYYY-MM-DD), sender, importance (H/M/L).
    Searches across subject, from_name, category, what, keywords fields."""
    oracle = get_oracle()
    if oracle is None:
        return "Audit trail requires cloud DB connection"

    cur = oracle.cursor()
    conditions = []
    params = {}

    if query:
        conditions.append("(LOWER(a.subject) LIKE :q OR LOWER(a.what) LIKE :q OR LOWER(a.keywords) LIKE :q)")
        params["q"] = f"%{query.lower()}%"
    if date:
        conditions.append("a.ts LIKE :dt")
        params["dt"] = f"{date}%"
    if sender:
        conditions.append("(LOWER(a.from_name) LIKE :snd OR LOWER(a.from_addr) LIKE :snd)")
        params["snd"] = f"%{sender.lower()}%"
    if importance:
        conditions.append("a.importance = :imp")
        params["imp"] = importance.upper()[:1]
    if workspace != "all":
        conditions.append("a.workspace_id = :ws")
        params["ws"] = workspace

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"""
        SELECT a.ts, a.folder, a.direction, a.from_name, a.subject,
               a.importance, a.category, a.is_suspicious, a.workspace_id
        FROM AUDIT_LOG a {where}
        ORDER BY a.ts DESC
        FETCH FIRST :lim ROWS ONLY
    """
    params["lim"] = limit

    cur.execute(sql, params)
    rows = cur.fetchall()

    if not rows:
        return f"No audit entries found"
    lines = [f"Audit trail ({len(rows)} entries):"]
    for r in rows:
        flag = " [!SUSPICIOUS]" if r[7] else ""
        lines.append(f"  {r[0][:16]} | {r[5] or '-'} | {r[3][:25]:25s} | {(r[4] or '')[:50]}{flag}")
    return "\n".join(lines)


@mcp.tool()
def memory_audit_stats(date: str = "", workspace: str = "all") -> str:
    """Get audit trail statistics. Optionally filter by date (YYYY-MM-DD or YYYY-MM) and workspace.
    Shows counts by importance, direction, category, and suspicious flags."""
    oracle = get_oracle()
    if oracle is None:
        return "Audit stats require cloud DB connection"

    cur = oracle.cursor()
    conditions = []
    params = {}

    if date:
        conditions.append("a.ts LIKE :dt")
        params["dt"] = f"{date}%"
    if workspace != "all":
        conditions.append("a.workspace_id = :ws")
        params["ws"] = workspace

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    lines = []

    # Total count
    cur.execute(f"SELECT COUNT(*) FROM AUDIT_LOG a {where}", params)
    total = cur.fetchone()[0]
    lines.append(f"Audit trail: {total} total entries")

    # By importance
    cur.execute(f"""
        SELECT importance, COUNT(*) FROM AUDIT_LOG a {where}
        GROUP BY importance ORDER BY importance
    """, params)
    lines.append("\nBy importance:")
    for r in cur.fetchall():
        label = {"H": "High", "M": "Medium", "L": "Low"}.get(r[0], r[0] or "?")
        lines.append(f"  {label}: {r[1]}")

    # By direction
    cur.execute(f"""
        SELECT direction, COUNT(*) FROM AUDIT_LOG a {where}
        GROUP BY direction ORDER BY direction
    """, params)
    lines.append("\nBy direction:")
    for r in cur.fetchall():
        lines.append(f"  {r[0] or '?'}: {r[1]}")

    # Suspicious count
    cur.execute(f"SELECT COUNT(*) FROM AUDIT_LOG a {where} AND is_suspicious = 1" if where else
                "SELECT COUNT(*) FROM AUDIT_LOG a WHERE is_suspicious = 1", params)
    sus = cur.fetchone()[0]
    lines.append(f"\nSuspicious: {sus}")

    # Top categories
    cur.execute(f"""
        SELECT category, COUNT(*) as cnt FROM AUDIT_LOG a {where}
        GROUP BY category ORDER BY cnt DESC FETCH FIRST 10 ROWS ONLY
    """, params)
    lines.append("\nTop categories:")
    for r in cur.fetchall():
        lines.append(f"  {r[0] or 'uncategorized'}: {r[1]}")

    return "\n".join(lines)


@mcp.tool()
def memory_daily_report(date: str = "", workspace: str = "all", limit: int = 7) -> str:
    """Get daily reports. Filter by date (YYYY-MM-DD) or get recent N days.
    Shows email counts, calendar events, high-priority items, and narrative summary."""
    oracle = get_oracle()
    if oracle is None:
        return "Daily reports require cloud DB connection"

    cur = oracle.cursor()

    if date:
        sql = """
            SELECT workspace_id, report_date, day_of_week,
                   email_count, inbox_count, sent_count, calendar_count,
                   h_count, m_count, l_count, suspicious_count,
                   top_senders, h_subjects, narrative
            FROM DAILY_REPORTS
            WHERE report_date = TO_DATE(:dt, 'YYYY-MM-DD')
        """
        params = {"dt": date}
        if workspace != "all":
            sql += " AND workspace_id = :ws"
            params["ws"] = workspace
        sql += " ORDER BY workspace_id"
    else:
        sql = """
            SELECT workspace_id, report_date, day_of_week,
                   email_count, inbox_count, sent_count, calendar_count,
                   h_count, m_count, l_count, suspicious_count,
                   top_senders, h_subjects, narrative
            FROM DAILY_REPORTS
        """
        params = {}
        if workspace != "all":
            sql += " WHERE workspace_id = :ws"
            params["ws"] = workspace
        sql += " ORDER BY report_date DESC FETCH FIRST :lim ROWS ONLY"
        params["lim"] = limit

    cur.execute(sql, params)
    rows = cur.fetchall()

    if not rows:
        return f"No daily reports found"

    lines = [f"Daily Reports ({len(rows)} entries):"]
    for r in rows:
        report_date = str(r[1])[:10] if r[1] else "?"
        lines.append(f"\n--- {report_date} ({r[2] or '?'}) [{r[0]}] ---")
        lines.append(f"  Email: {r[3]} total (inbox:{r[4]} sent:{r[5]}) | Calendar: {r[6]}")
        lines.append(f"  Priority: H={r[7]} M={r[8]} L={r[9]} | Suspicious: {r[10]}")
        if r[13]:  # narrative
            narrative = str(r[13])[:300]
            lines.append(f"  Summary: {narrative}")
        if r[12]:  # h_subjects
            lines.append(f"  High-priority: {str(r[12])[:200]}")

    return "\n".join(lines)


@mcp.tool()
def memory_activity_log(
    agent: str = "", action: str = "", workspace: str = "all", limit: int = 20
) -> str:
    """View agent activity log. Filter by agent name, action type, or workspace.
    Shows what agents (hr_patrol, pm_patrol, claude, etc.) have been doing."""
    oracle = get_oracle()
    if oracle is None:
        return "Activity log requires cloud DB connection"

    cur = oracle.cursor()
    conditions = []
    params = {}

    if agent:
        conditions.append("LOWER(a.agent) LIKE :ag")
        params["ag"] = f"%{agent.lower()}%"
    if action:
        conditions.append("LOWER(a.action) LIKE :act")
        params["act"] = f"%{action.lower()}%"
    if workspace != "all":
        conditions.append("a.workspace_id = :ws")
        params["ws"] = workspace

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"""
        SELECT a.logged_at, a.log_type, a.agent, a.action, a.task_type,
               a.target, a.result_status, a.workspace_id
        FROM ACTIVITY_LOG a {where}
        ORDER BY a.logged_at DESC
        FETCH FIRST :lim ROWS ONLY
    """
    params["lim"] = limit

    cur.execute(sql, params)
    rows = cur.fetchall()

    if not rows:
        return "No activity log entries found"
    lines = [f"Activity log ({len(rows)} entries):"]
    for r in rows:
        ts = str(r[0])[:16] if r[0] else "?"
        action_str = r[3] or r[4] or "?"
        target = (r[5] or "")[:40]
        status = f" [{r[6]}]" if r[6] else ""
        lines.append(f"  {ts} | {r[2] or '?':15s} | {action_str:15s} | {target}{status}")
    return "\n".join(lines)


# ============================================================
# ADMIN TOOLS
# ============================================================

@mcp.tool()
def memory_status() -> str:
    """Get system status: local counts + Oracle sync status."""
    from .config import load_config
    config = load_config()
    lines = [f"MCP Memory Server v0.1.0", f"Workspace: {detect_workspace()}"]

    # Local summary
    try:
        summary = memory_get_summary()
        lines.append(f"Local: {summary}")
    except Exception as e:
        lines.append(f"Local: error - {e}")

    # Oracle status
    oracle = get_oracle()
    if oracle:
        cur = oracle.cursor()
        cur.execute("SELECT COUNT(*) FROM WORKSPACES WHERE is_active = 1")
        ws_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM KNOWLEDGE_ITEMS")
        ki_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM KNOWLEDGE_ITEMS WHERE embedding IS NOT NULL")
        emb_count = cur.fetchone()[0]
        cur.execute("""
            SELECT MAX(completed_at) FROM SYNC_LOG
        """)
        last_sync = cur.fetchone()[0]
        # Trail counts
        audit_count = 0
        report_count = 0
        activity_count = 0
        try:
            cur.execute("SELECT COUNT(*) FROM AUDIT_LOG")
            audit_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM DAILY_REPORTS")
            report_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM ACTIVITY_LOG")
            activity_count = cur.fetchone()[0]
        except Exception:
            pass

        lines.append(f"Oracle: {ws_count} workspaces, {ki_count} knowledge ({emb_count} embedded)")
        lines.append(f"Trail: {audit_count} audit entries, {report_count} daily reports, {activity_count} activity logs")
        lines.append(f"Last sync: {last_sync}")
    else:
        lines.append("Oracle: not connected")

    # Embedding config
    lines.append(f"Embeddings: {config['embedding']['provider']}")

    return "\n".join(lines)


@mcp.tool()
def memory_compact(workspace: str = "current") -> str:
    """Compact: summarize session.md, extract key items to SQLite, trim session."""
    ws = detect_workspace() if workspace == "current" else workspace
    from .config import load_config
    config = load_config()

    # Find session.md
    if ws == "claude-setup":
        session_path = Path(config["claude_setup_dir"]) / ".claude-memory" / "session.md"
    else:
        try:
            with open(config["workspace_map"]) as f:
                ws_map = json.load(f)
            session_path = Path(config["workspace_root"]) / ws_map[ws] / ".claude-memory" / "session.md"
        except (FileNotFoundError, KeyError):
            return f"Cannot find session.md for [{ws}]"

    if not session_path.exists():
        return f"No session.md found at {session_path}"

    content = session_path.read_text(encoding="utf-8")
    line_count = len(content.splitlines())

    return (
        f"[{ws}] session.md has {line_count} lines.\n"
        f"Compact should be triggered by the agent (read session.md, extract items via memory_record_*, "
        f"then trim session.md). This tool reports status only."
    )


@mcp.tool()
def memory_oracle_summary() -> str:
    """Cross-workspace summary from Oracle (all workspaces, all domains)."""
    oracle = get_oracle()
    if oracle is None:
        return "Oracle not connected"

    cur = oracle.cursor()
    cur.execute("""
        SELECT w.workspace_id, w.domain,
            (SELECT COUNT(*) FROM DECISIONS d WHERE d.workspace_id = w.workspace_id),
            (SELECT COUNT(*) FROM RESOLVED r WHERE r.workspace_id = w.workspace_id),
            (SELECT COUNT(*) FROM OPEN_QUESTIONS q WHERE q.workspace_id = w.workspace_id),
            (SELECT COUNT(*) FROM KNOWLEDGE_ITEMS k WHERE k.workspace_id = w.workspace_id)
        FROM WORKSPACES w WHERE w.is_active = 1
        ORDER BY w.domain, w.workspace_id
    """)
    rows = cur.fetchall()

    lines = [f"{'Workspace':<35} {'Domain':<10} {'Dec':>4} {'Res':>4} {'Q':>4} {'Know':>5}"]
    lines.append("-" * 70)
    for r in rows:
        lines.append(f"{r[0]:<35} {r[1]:<10} {r[2]:>4} {r[3]:>4} {r[4]:>4} {r[5]:>5}")
    return "\n".join(lines)


# ============================================================
# Entry point
# ============================================================

def main():
    if "--decay" in sys.argv:
        # Run decay job (called by sync-all.ps1)
        from .config import load_config
        config = load_config()
        try:
            with open(config["workspace_map"]) as f:
                ws_map = json.load(f)
            total = 0
            for ws_id in list(ws_map.keys()) + ["claude-setup"]:
                try:
                    n = run_decay(ws_id)
                    if n:
                        print(f"  [{ws_id}] decayed {n} items")
                    total += n
                except Exception:
                    pass
            print(f"Decay complete: {total} items decayed")
        except Exception as e:
            print(f"Decay error: {e}")
    elif "--http" in sys.argv:
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8787)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
