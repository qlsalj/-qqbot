import threading
import time
import logging
import sqlite3
from db import get_db_connection

def stamina_recovery():
    RECOVERY_INTERVAL = 600  # 10分钟
    RECOVERY_AMOUNT = 10
    MOOD_ADJUST_INTERVAL = 3600  # 1小时
    MOOD_ADJUST_AMOUNT = 1
    logging.info("Stamina recovery and mood adjustment thread started")
    while True:
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT username, stamina, mood, last_stamina_update FROM user_status")
            users = c.fetchall()
            current_time = time.time()
            updates = []
            for username, stamina, mood, last_update in users:
                elapsed = current_time - last_update
                # 体力恢复
                recovery_cycles = int(elapsed // RECOVERY_INTERVAL)
                new_stamina = stamina
                if recovery_cycles > 0 and stamina < 100:
                    recovery_total = recovery_cycles * RECOVERY_AMOUNT
                    new_stamina = min(100, stamina + recovery_total)
                # 心情趋向50
                mood_cycles = int(elapsed // MOOD_ADJUST_INTERVAL)
                new_mood = mood
                if mood_cycles > 0:
                    if mood > 50:
                        new_mood = max(50, mood - mood_cycles * MOOD_ADJUST_AMOUNT)
                    elif mood < 50:
                        new_mood = min(50, mood + mood_cycles * MOOD_ADJUST_AMOUNT)
                if new_stamina != stamina or new_mood != mood:
                    updates.append((new_stamina, new_mood, current_time, username))
            if updates:
                c.executemany("UPDATE user_status SET stamina = ?, mood = ?, last_stamina_update = ? WHERE username = ?", updates)
                logging.info(f"Updated stamina and mood for {len(updates)} users")
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Stamina and mood adjustment error: {e}")
        time.sleep(RECOVERY_INTERVAL)