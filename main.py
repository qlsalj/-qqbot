import threading
import time
import uvicorn
import logging
from web import run_fastapi, run_gradio
from db import init_db
from status import stamina_recovery

# 配置日志
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    logging.info("Starting application")
    try:
        init_db()  # 先初始化数据库
        logging.info("Database initialized successfully")
        time.sleep(1)  # 延迟1秒，确保数据库初始化完成
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        raise
    logging.info("Starting stamina recovery thread")
    threading.Thread(target=stamina_recovery, daemon=True).start()
    logging.info("Starting FastAPI server on port 7862")
    threading.Thread(target=run_fastapi, daemon=True).start()
    logging.info("Starting Gradio in main thread")
    run_gradio()