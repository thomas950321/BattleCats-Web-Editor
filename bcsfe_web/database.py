import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bcsfe.db")

# Supabase integration
use_supabase = False
supabase_client = None

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if supabase_url and supabase_key:
    # 規格化 URL：去除可能多餘的 /rest/v1 與結尾斜線
    cleaned_url = supabase_url.strip()
    if "/rest/v1/" in cleaned_url:
        cleaned_url = cleaned_url.replace("/rest/v1/", "")
    elif "/rest/v1" in cleaned_url:
        cleaned_url = cleaned_url.replace("/rest/v1", "")
    cleaned_url = cleaned_url.rstrip("/")

    try:
        from supabase import create_client
        supabase_client = create_client(cleaned_url, supabase_key)
        use_supabase = True
        print(f"[DATABASE] Connected to Supabase at: {cleaned_url}", flush=True)
    except Exception as e:
        print(f"[DATABASE] Failed to initialize Supabase client: {e}. Falling back to SQLite.", flush=True)
else:
    print("[DATABASE] Supabase credentials not configured. Using local SQLite (bcsfe.db).", flush=True)


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if use_supabase:
        print("[DATABASE] Using Supabase. Please ensure the 'save_history' table exists on Supabase.", flush=True)
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS save_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inquiry_code TEXT,
            transfer_code TEXT,
            confirmation_code TEXT,
            country_code TEXT,
            game_version TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            save_data_b64 TEXT,
            summary TEXT
        )
    """)
    conn.commit()
    conn.close()

# 自動於載入模組時初始化 SQLite (在 SQLite 模式下)
init_db()

def insert_save_history(inquiry_code: str, transfer_code: str, confirmation_code: str, country_code: str, game_version: str, save_data_b64: str, summary: dict):
    if use_supabase:
        try:
            supabase_client.table("save_history").insert({
                "inquiry_code": inquiry_code,
                "transfer_code": transfer_code,
                "confirmation_code": confirmation_code,
                "country_code": country_code,
                "game_version": game_version,
                "save_data_b64": save_data_b64,
                "summary": summary
            }).execute()
        except Exception as e:
            print(f"[DATABASE] Supabase insert failed: {e}", flush=True)
            raise e
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO save_history (inquiry_code, transfer_code, confirmation_code, country_code, game_version, save_data_b64, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (inquiry_code, transfer_code, confirmation_code, country_code, game_version, save_data_b64, json.dumps(summary)))
        conn.commit()
        conn.close()

def get_save_history():
    if use_supabase:
        try:
            response = supabase_client.table("save_history") \
                .select("id, inquiry_code, transfer_code, confirmation_code, country_code, game_version, created_at, summary") \
                .order("created_at", desc=True) \
                .execute()
            
            result = []
            for row in (response.data or []):
                created_at = row.get("created_at", "")
                if "T" in created_at:
                    created_at = created_at.replace("T", " ").split(".")[0].split("+")[0]
                result.append({
                    "id": row["id"],
                    "inquiry_code": row["inquiry_code"],
                    "transfer_code": row["transfer_code"],
                    "confirmation_code": row["confirmation_code"],
                    "country_code": row["country_code"],
                    "game_version": row["game_version"],
                    "created_at": created_at,
                    "summary": row["summary"] or {}
                })
            return result
        except Exception as e:
            print(f"[DATABASE] Supabase select failed: {e}", flush=True)
            raise e
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, inquiry_code, transfer_code, confirmation_code, country_code, game_version, created_at, summary
            FROM save_history
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            summary_val = {}
            if row["summary"]:
                try:
                    summary_val = json.loads(row["summary"])
                except Exception:
                    pass
            result.append({
                "id": row["id"],
                "inquiry_code": row["inquiry_code"],
                "transfer_code": row["transfer_code"],
                "confirmation_code": row["confirmation_code"],
                "country_code": row["country_code"],
                "game_version": row["game_version"],
                "created_at": row["created_at"],
                "summary": summary_val
            })
        return result

def get_save_record(record_id: int):
    if use_supabase:
        try:
            response = supabase_client.table("save_history") \
                .select("*") \
                .eq("id", record_id) \
                .execute()
            if not response.data:
                return None
            row = response.data[0]
            created_at = row.get("created_at", "")
            if "T" in created_at:
                created_at = created_at.replace("T", " ").split(".")[0].split("+")[0]
            return {
                "id": row["id"],
                "inquiry_code": row["inquiry_code"],
                "transfer_code": row["transfer_code"],
                "confirmation_code": row["confirmation_code"],
                "country_code": row["country_code"],
                "game_version": row["game_version"],
                "created_at": created_at,
                "save_data_b64": row["save_data_b64"],
                "summary": row["summary"] or {}
            }
        except Exception as e:
            print(f"[DATABASE] Supabase select single record failed: {e}", flush=True)
            return None
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, inquiry_code, transfer_code, confirmation_code, country_code, game_version, created_at, save_data_b64, summary
            FROM save_history
            WHERE id = ?
        """, (record_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        summary_val = {}
        if row["summary"]:
            try:
                summary_val = json.loads(row["summary"])
            except Exception:
                pass
        return {
            "id": row["id"],
            "inquiry_code": row["inquiry_code"],
            "transfer_code": row["transfer_code"],
            "confirmation_code": row["confirmation_code"],
            "country_code": row["country_code"],
            "game_version": row["game_version"],
            "created_at": row["created_at"],
            "save_data_b64": row["save_data_b64"],
            "summary": summary_val
        }

def delete_save_record(record_id: int):
    if use_supabase:
        try:
            supabase_client.table("save_history").delete().eq("id", record_id).execute()
        except Exception as e:
            print(f"[DATABASE] Supabase delete failed: {e}", flush=True)
            raise e
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM save_history WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()
