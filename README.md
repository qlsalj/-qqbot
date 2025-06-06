可本地运行、私有部署。
---

## 🛠 安装要求

* **Python 版本**：Python 3.8 或更高版本

* **依赖库**（通过 pip 安装）：

  * `ollama`
  * `fastapi`
  * `gradio`
  * `uvicorn`
  * `python-dotenv`
  * `sqlite3`（Python 内置模块，无需安装）

* **其他软件**：

  * **Ollama 服务**：用于本地运行 AI 模型。请从 [Ollama 官网](https://ollama.com) 下载并安装，并确保服务运行在 `http://localhost:11434`。

---

## 🚀 快速开始

### 1️⃣ 克隆项目

```bash
git clone https://github.com/qlsalj/-qqbot
cd -qqbot
```

### 2️⃣ 安装依赖

**推荐使用虚拟环境：**

```bash
python -m venv venv
# macOS/Linux
source venv/bin/activate
# Windows
venv\Scripts\activate
```

**安装项目依赖：**

```bash
pip install ollama fastapi gradio uvicorn python-dotenv
```

---

### 3️⃣ 配置环境变量

在项目根目录创建 `.env` 文件，用于存放敏感信息：

```env
BOT_QQ=你的QQ号码
MODEL_NAME=qwen3
```

> ⚠️ `.env` 文件已被加入 `.gitignore`，请勿提交到 Git 仓库中。

---

### 4️⃣ 启动应用

```bash
python main.py
```

该命令将初始化数据库并启动本地服务。

---

### 5️⃣ 使用方式

#### ✅ 网页端交互

打开浏览器访问：
[http://127.0.0.1:7861](http://127.0.0.1:7861)

首次登录默认账户：

* 用户名：`visit`
* 密码：`123`

成功登录后即可输入消息与猫娘互动。

#### ✅ QQ 机器人交互（如已集成）

在群聊或私聊中 @机器人，并发送消息（如“喵\~摸头”），猫娘将自动进行回复。

---

## 📂 项目结构

```
├── chat.py           # 对话逻辑
├── config.py         # 配置中心（读取 .env）
├── db.py             # 数据库读写逻辑
├── main.py           # 启动脚本
├── status.py         # 状态管理模块
├── web.py            # Web 接口（Gradio + FastAPI）
├── .env              # 私密变量（不应提交）
├── .gitignore        # Git 忽略配置
├── catmaid.db        # 数据库存储（首次运行自动生成）
└── README.md         # 使用说明文档
```

---

## 🔐 安全提示

* 请不要将 `.env` 中的 `BOT_QQ` 等信息上传至公网仓库。
* 使用公网访问建议通过身份验证、加密隧道或部署于可信服务器中。

---
