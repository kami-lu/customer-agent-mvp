# 智能客服 Agent MVP

这是一个面试展示用的最小闭环版本，目标是把“智能客服 Agent”真实跑起来，并能清楚解释每个模块。

## 已实现能力

- 意图路由：商品咨询、订单查询、售后问题、普通问题
- 结构化路由：输出 `intent`、`tool_name`、`slots`、`route_source`
- 工具调用：根据意图查询 SQLite 商品表、订单表、FAQ 表
- 轻量 RAG：基于本地知识库 chunk 做 TF-IDF 相似度检索
- 回复生成：没有 API Key 时使用规则模板，有 `DEEPSEEK_API_KEY` 时调用 DeepSeek 生成客服回复
- 会话存储：把用户问题和助手回复写入 SQLite
- 会话管理：支持会话列表和历史消息查询
- SQLAlchemy ORM 数据层：默认 SQLite，可通过 `DATABASE_URL` 切换数据库
- Alembic 数据库迁移：支持表结构版本化管理
- FastAPI 接口：提供 `/health`、`/chat` 和 `/docs`

## 项目结构

```text
mvp_agent/
  app.py              # FastAPI 路由和服务入口
  agent.py            # Router、工具调用、RAG 检索、DeepSeek 调用
  db.py               # SQLite 建表、seed 数据、会话和消息读写
  models.py           # Product、Order、FAQ、KnowledgeChunk、Conversation、Message ORM 模型
  web.py              # 浏览器聊天页面
  README.md           # 运行说明
  .env.example        # 可选的大模型配置示例
```

## 安装依赖

如果当前环境还没有 FastAPI：

```bash
pip install -r mvp_agent/requirements.txt
```

## 启动

```bash
python -m mvp_agent.app
```

默认数据库是本地 SQLite：

```text
mvp_agent/customer_agent.sqlite3
```

也可以用环境变量指定其他数据库 URL：

```powershell
$env:DATABASE_URL="sqlite:///./mvp_agent/customer_agent.sqlite3"
```

## 数据库迁移

创建或升级表结构：

```bash
alembic upgrade head
```

如果本地已经存在由 `init_db()` 自动创建的 SQLite 文件，想完整体验迁移流程，可以先删除运行库：

```powershell
Remove-Item .\mvp_agent\customer_agent.sqlite3
alembic upgrade head
python -m mvp_agent.app
```

说明：`alembic upgrade head` 负责表结构，`python -m mvp_agent.app` 启动时会继续补充 seed 示例数据。

默认服务地址：

```text
http://127.0.0.1:8010
```

浏览器页面：

```text
http://127.0.0.1:8010/chat
```

Swagger 文档：

```text
http://127.0.0.1:8010/docs
```

会话接口：

```text
GET /conversations
GET /conversations/{conversation_id}/messages
```

## 测试

PowerShell：

```powershell
$body = @{ query = "推荐一款智能门锁"; conversation_id = "demo-1" } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8010/chat -Method Post -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

更多测试问题：

```text
推荐一款智能门锁
查一下订单 SO20260611001 的物流
智能门锁坏了怎么保修
智能门锁怎么安装
扫地机器人怎么维护
你能做什么
```

`POST /chat` 会返回结构化路由结果，例如：

```json
{
  "intent": "order",
  "tool_name": "search_order",
  "slots": {"order_id": "SO20260611001"},
  "route_source": "rule"
}
```

知识库类问题会走 RAG 工具：

```json
{
  "intent": "rag",
  "tool_name": "search_knowledge",
  "tool_context": {
    "chunks": [
      {
        "title": "智能门锁安装说明",
        "source": "install_policy.md",
        "score": 0.42
      }
    ]
  }
}
```

## 可选：接入 DeepSeek

设置环境变量后，系统会用 DeepSeek 基于工具查询结果生成回复；不设置也能用规则模板完整演示。

```powershell
$env:DEEPSEEK_API_KEY="your_api_key"
$env:DEEPSEEK_BASE_URL="https://api.deepseek.com"
$env:DEEPSEEK_MODEL="deepseek-chat"
python -m mvp_agent.app
```

## 面试讲法

这个 MVP 对应完整 Agent 项目的最小可运行切片：

1. Router 判断用户意图。
2. 根据意图选择工具。
3. 工具查询业务数据库。
4. LLM 或模板基于工具结果生成回复。
5. 会话记录落库，便于后续做上下文记忆和日志分析。
