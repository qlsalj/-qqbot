import sqlite3
import time
import re
import logging
from ollama import Client
from db import get_db_connection, get_user_status, update_status, save_chat_history, get_chat_history, trim_chat_history
from config import MAX_STATUS_VALUE, SYSTEM_PROMPT, MODEL_NAME, BOT_QQ, INITIAL_AFFECTION, INITIAL_STAMINA, INITIAL_MOOD, MAX_CHAT_HISTORY, MAX_HISTORY_CHARS

# 初始化 ollama
ollama = Client(host='http://localhost:11434')

def sanitize_input(text):
    return re.sub(r'[^\w\s]', '', text)

def validate_username(username):
    if not username or not re.match(r'^[a-zA-Z0-9_]{1,50}$', username):
        return False
    return True

def parse_message_content(message):
    if isinstance(message, str):
        return sanitize_input(message.strip())
    if isinstance(message, list):
        text = ''.join(segment.get('data', {}).get('text', '') 
                       for segment in message if segment.get('type') == 'text')
        return sanitize_input(text.strip())
    logging.warning(f"Unsupported message format: {message}")
    return ""

def is_at_bot(message):
    if isinstance(message, list):
        for segment in message:
            if segment.get("type") == "at" and segment.get("data", {}).get("qq") == BOT_QQ:
                return True
    return False

def remove_think_blocks(text):
    # 移除 <think>...</think> 代码块
    return re.sub(r'<think>[\s\S]*?</think>', '', text).strip()

def extract_status_changes(reply):
    # 从 AI 回复中提取状态变化，如 [affection: +5], [stamina: -2], [mood: +3]
    patterns = {
        'affection': r'\[affection:\s*([+-]?\d+)\]',
        'stamina': r'\[stamina:\s*([+-]?\d+)\]',
        'mood': r'\[mood:\s*([+-]?\d+)\]'
    }
    changes = {'affection': 0, 'stamina': -2, 'mood': 0}  # 默认体力消耗 -2
    for key, pattern in patterns.items():
        match = re.search(pattern, reply)
        if match:
            changes[key] = int(match.group(1))
    return changes

def chat_with_model(user_input, username=None):
    logging.debug(f"Chat input: {user_input}, username: {username}")
    if not username or not validate_username(username):
        logging.warning("Invalid or missing username")
        return "喵~主人请先登录哦！"

    status = get_user_status(username)
    if status["stamina"] <= 0:
        return (f"喵呜...咱喵太累了喵，没力气说话了，要休息一下喵~💤\n"
                f"❤️ 好感度：{status['affection']}/{MAX_STATUS_VALUE}\n"
                f"⚡ 体力值：0/{MAX_STATUS_VALUE}\n"
                f"😺 心情值：{status['mood']}/{MAX_STATUS_VALUE}")

    parsed_input = parse_message_content(user_input)
    if not parsed_input:
        logging.warning("Empty or invalid message content")
        return "喵~主人你的消息好像有问题哦！"

    local_chat_history = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *get_chat_history(username, limit=MAX_CHAT_HISTORY),
        {"role": "system", "content": 
            f"当前状态：❤️好感度：{status['affection']}/{MAX_STATUS_VALUE}，⚡体力值：{status['stamina']}/{MAX_STATUS_VALUE}，😺心情值：{status['mood']}/{MAX_STATUS_VALUE}。"
            f"请在回复中包含状态变化，格式为 [affection: +5], [stamina: -2], [mood: +3]，并确保值合理（总和在0-100之间）。"},
        {"role": "user", "content": parsed_input}
    ]

    try:
        response = ollama.chat(model=MODEL_NAME, messages=local_chat_history)
        reply = response['message']['content']
        clean_reply = remove_think_blocks(reply)
        
        # 提取状态变化
        changes = extract_status_changes(reply)
        new_status = {
            'affection': max(0, min(MAX_STATUS_VALUE, status['affection'] + changes['affection'])),
            'stamina': max(0, min(MAX_STATUS_VALUE, status['stamina'] + changes['stamina'])),
            'mood': max(0, min(MAX_STATUS_VALUE, status['mood'] + changes['mood']))
        }
        
        # 更新状态
        update_status(username, delta_stamina=new_status['stamina'] - status['stamina'],
                      delta_affection=new_status['affection'] - status['affection'],
                      delta_mood=new_status['mood'] - status['mood'])

        save_chat_history(username, "user", parsed_input)
        save_chat_history(username, "assistant", clean_reply)
        trim_chat_history(username, max_history=MAX_CHAT_HISTORY, max_chars=MAX_HISTORY_CHARS)
        
        return (f"{clean_reply}\n"
                f"❤️ 好感度：{new_status['affection']}/{MAX_STATUS_VALUE}\n"
                f"⚡ 体力值：{new_status['stamina']}/{MAX_STATUS_VALUE}\n"
                f"😺 心情值：{new_status['mood']}/{MAX_STATUS_VALUE}")
    except Exception as e:
        logging.error(f"Ollama error: {e}")
        return "喵~服务器有点小脾气，请稍后再试哦！"

def reset_chat(username=None):
    if not username or not validate_username(username):
        logging.warning("Invalid or missing username")
        return "喵~主人请先登录哦！"

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM user_status WHERE username = ?", (username,))
    c.execute("DELETE FROM chat_history WHERE username = ?", (username,))
    c.execute("INSERT INTO user_status (username, affection, stamina, mood, last_stamina_update) VALUES (?, ?, ?, ?, ?)",
              (username, INITIAL_AFFECTION, INITIAL_STAMINA, INITIAL_MOOD, time.time()))
    conn.commit()
    conn.close()
    logging.info(f"Chat history and status reset for {username}")
    return "已重置聊天和状态~喵~"