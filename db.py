import sqlite3
import logging
import time
from config import INITIAL_AFFECTION, INITIAL_STAMINA, INITIAL_MOOD

def get_db_connection():
    # 使用绝对路径
    conn = sqlite3.connect('E:/好玩爱玩/ollama/project/catmaid.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_status (
            username TEXT PRIMARY KEY,
            affection INTEGER DEFAULT 50,
            stamina INTEGER DEFAULT 100,
            mood INTEGER DEFAULT 50,
            last_stamina_update REAL DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT,
            content TEXT,
            timestamp REAL
        )
    ''')
    conn.commit()
    conn.close()
    logging.info("SQLite database initialized")

def get_user_status(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT affection, stamina, mood, last_stamina_update FROM user_status WHERE username = ?", (username,))
    result = c.fetchone()
    if result:
        status = {"affection": result[0], "stamina": result[1], "mood": result[2], "last_stamina_update": result[3]}
    else:
        status = {"affection": INITIAL_AFFECTION, "stamina": INITIAL_STAMINA, "mood": INITIAL_MOOD, "last_stamina_update": 0}
        c.execute("INSERT INTO user_status (username, affection, stamina, mood, last_stamina_update) VALUES (?, ?, ?, ?, ?)",
                  (username, status["affection"], status["stamina"], status["mood"], status["last_stamina_update"]))
        conn.commit()
    conn.close()
    logging.debug(f"Retrieved status for {username}: {status}")
    return status

def update_status(username, delta_stamina=0, delta_affection=0, delta_mood=0):
    status = get_user_status(username)
    new_stamina = max(0, min(100, status["stamina"] + delta_stamina))
    new_affection = max(0, min(100, status["affection"] + delta_affection))
    new_mood = max(0, min(100, status["mood"] + delta_mood))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE user_status SET affection = ?, stamina = ?, mood = ?, last_stamina_update = ? WHERE username = ?",
              (new_affection, new_stamina, new_mood, status["last_stamina_update"], username))
    conn.commit()
    conn.close()
    logging.info(f"Updated status for {username}: affection={new_affection}, stamina={new_stamina}, mood={new_mood}")

def save_chat_history(username, role, content):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO chat_history (username, role, content, timestamp) VALUES (?, ?, ?, ?)",
              (username, role, content, time.time()))
    conn.commit()
    conn.close()

def get_chat_history(username, limit=8):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT role, content FROM chat_history WHERE username = ? ORDER BY timestamp DESC LIMIT ?",
              (username, limit))
    history = [{"role": row[0], "content": row[1]} for row in c.fetchall()]
    conn.close()
    return history[::-1]

def trim_chat_history(username, max_history=8, max_chars=10000):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, content FROM chat_history WHERE username = ? ORDER BY timestamp DESC", (username,))
    rows = c.fetchall()
    total_chars = sum(len(row[1]) for row in rows)
    if len(rows) > max_history or total_chars > max_chars:
        delete_ids = [row[0] for row in rows[max_history:]]
        if delete_ids:
            c.executemany("DELETE FROM chat_history WHERE id = ?", [(id,) for id in delete_ids])
            conn.commit()
            logging.info(f"Trimmed chat history for {username}: deleted {len(delete_ids)} messages")
    conn.close()