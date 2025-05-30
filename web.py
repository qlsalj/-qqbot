from fastapi import FastAPI, WebSocket
import uvicorn
import gradio as gr
import json
import logging
from chat import chat_with_model, is_at_bot, parse_message_content, reset_chat

app = FastAPI()

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logging.info("WebSocket connection established")
    try:
        while True:
            try:
                data = await websocket.receive()
                if isinstance(data, dict) and 'text' in data:
                    data = data['text']
                elif not isinstance(data, str):
                    logging.error(f"Received non-string data: {data}")
                    continue

                logging.debug(f"WebSocket received: {data}")
                try:
                    message = json.loads(data)
                except json.JSONDecodeError as e:
                    logging.error(f"JSON decode error: {e}")
                    continue

                if message.get("post_type") == "message":
                    user_input = message.get("message")
                    sender = str(message.get("sender", {}).get("user_id", "unknown"))
                    message_type = message.get("message_type")
                    group_id = str(message.get("group_id", ""))

                    if message_type == "group" and group_id:
                        if not is_at_bot(user_input):
                            logging.debug(f"Ignoring group message from {sender} in group {group_id}: No @mention")
                            continue
                        logging.info(f"Processing group message from {sender} in group {group_id}: {user_input}")
                        try:
                            response = chat_with_model(user_input, username=sender)
                            await websocket.send_json({
                                "action": "send_group_msg",
                                "params": {
                                    "group_id": group_id,
                                    "message": response
                                }
                            })
                        except Exception as e:
                            logging.error(f"Error processing group message: {e}")
                            await websocket.send_json({
                                "action": "send_group_msg",
                                "params": {
                                    "group_id": group_id,
                                    "message": "喵~出错了，请稍后再试！"
                                }
                            })
                            continue
                    elif message_type == "private":
                        logging.info(f"Processing private message from {sender}: {user_input}")
                        try:
                            response = chat_with_model(user_input, username=sender)
                            await websocket.send_json({
                                "action": "send_msg",
                                "params": {
                                    "user_id": sender,
                                    "message": response
                                }
                            })
                        except Exception as e:
                            logging.error(f"Error processing private message: {e}")
                            await websocket.send_json({
                                "action": "send_msg",
                                "params": {
                                    "user_id": sender,
                                    "message": "喵~出错了，请稍后再试！"
                                }
                            })
                            continue
            except Exception as e:
                logging.error(f"WebSocket message handling error: {e}")
                continue  # 继续处理下一条消息
    except Exception as e:
        logging.error(f"WebSocket connection error: {e}")
    finally:
        await websocket.close()
        logging.info("WebSocket connection closed")

def run_fastapi():
    uvicorn.run(app, host="127.0.0.1", port=7862)

def run_gradio():
    with gr.Blocks(
        theme=gr.themes.Base(primary_hue="blue", secondary_hue="cyan", neutral_hue="slate"),
        css="""
        .gradio-container { 
            background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%); 
            font-family: 'Orbitron', sans-serif; 
            color: #e0e7ff; 
        }
        .gr-button { 
            border-radius: 8px !important; 
            background: linear-gradient(45deg, #3b82f6, #06b6d4) !important; 
            color: #ffffff !important; 
            border: 1px solid #60a5fa !important; 
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.5); 
            transition: all 0.3s ease; 
        }
        .gr-button:hover { 
            background: linear-gradient(45deg, #2563eb, #0891b2) !important; 
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.8); 
            transform: translateY(-2px); 
        }
        .gr-textbox { 
            border-radius: 8px !important; 
            border: 1px solid #60a5fa !important; 
            background: #1e293b !important; 
            color: #e0e7ff !important; 
        }
        .gr-textbox label { 
            color: #60a5fa !important; 
            font-weight: 600; 
        }
        .title { 
            text-align: center; 
            color: #3b82f6; 
            text-shadow: 0 0 10px rgba(59, 130, 246, 0.7); 
        }
        .subtitle { 
            text-align: center; 
            color: #94a3b8; 
            font-style: italic; 
        }
        .footer::before { 
            content: '⚡️ Powered by xAI & NapCatQQ ⚡️'; 
            display: block; 
            text-align: center; 
            color: #60a5fa; 
            padding: 10px; 
        }
        """
    ) as demo:
        username_state = gr.State(None)
        
        def on_login(request: gr.Request):
            logging.info(f"User login: {request.username}")
            return request.username if request.username else None

        gr.Markdown("# ⚡️ 赛博猫娘助手 ⚡️", elem_classes=["title"])
        gr.Markdown("欢迎进入未来世界，和高科技猫娘互动吧~喵~", elem_classes=["subtitle"])
        
        with gr.Row():
            chat_box = gr.Textbox(label="输入指令喵~", placeholder="在这输入你的消息，开启赛博冒险！", lines=2)
        output_box = gr.Textbox(label="猫娘的回应喵~", lines=5, interactive=False)
        
        with gr.Row():
            send_btn = gr.Button("发送指令")
            reset_btn = gr.Button("重置对话")
        
        demo.load(fn=on_login, inputs=None, outputs=username_state)
        send_btn.click(chat_with_model, inputs=[chat_box, username_state], outputs=output_box)
        reset_btn.click(reset_chat, inputs=username_state, outputs=output_box)

        logging.info("Starting Gradio server")
        demo.launch(server_name="127.0.0.1", server_port=7861, auth=("visit", "123"), auth_message="请输入用户名和密码进入赛博猫娘世界喵~", debug=True)