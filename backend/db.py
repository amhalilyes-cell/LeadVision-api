import os
import sqlite3
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join("data", "plans.db")

def _conn():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    con = _conn()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        niche TEXT NOT NULL,
        objective TEXT NOT NULL,
        threshold_vpd INTEGER NOT NULL,
        top_k INTEGER NOT NULL,
        ideas INTEGER NOT NULL,
        days INTEGER NOT NULL,
        plan_json_path TEXT NOT NULL,
        plan_md_path TEXT NOT NULL,
        plan_ui_json_path TEXT NOT NULL
    )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_plans_niche_obj ON plans(niche, objective)")
    con.commit()
    con.close()

def insert_plan(row: Dict[str, Any]) -> int:
    con = _conn()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO plans (
        created_at, niche, objective, threshold_vpd, top_k, ideas, days,
        plan_json_path, plan_md_path, plan_ui_json_path
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        row["created_at"], row["niche"], row["objective"], row["threshold_vpd"], row["top_k"], row["ideas"], row["days"],
        row["plan_json_path"], row["plan_md_path"], row["plan_ui_json_path"]
    ))
    con.commit()
    plan_id = cur.lastrowid
    con.close()
    return plan_id

def list_plans(limit: int = 20) -> List[Dict[str, Any]]:
    con = _conn()
    cur = con.cursor()
    cur.execute("""
    SELECT id, created_at, niche, objective, threshold_vpd, top_k, ideas, days,
           plan_json_path, plan_md_path, plan_ui_json_path
    FROM plans
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    con.close()
    keys = ["id","created_at","niche","objective","threshold_vpd","top_k","ideas","days","plan_json_path","plan_md_path","plan_ui_json_path"]
    return [dict(zip(keys, r)) for r in rows]

def get_plan(plan_id: int) -> Optional[Dict[str, Any]]:
    con = _conn()
    cur = con.cursor()
    cur.execute("""
    SELECT id, created_at, niche, objective, threshold_vpd, top_k, ideas, days,
           plan_json_path, plan_md_path, plan_ui_json_path
    FROM plans
    WHERE id = ?
    """, (plan_id,))
    r = cur.fetchone()
    con.close()
    if not r:
        return None
    keys = ["id","created_at","niche","objective","threshold_vpd","top_k","ideas","days","plan_json_path","plan_md_path","plan_ui_json_path"]
    return dict(zip(keys, r))