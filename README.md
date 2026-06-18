# 智能客服 Agent MVP

一个可运行的智能家居电商客服 Agent MVP，重点展示 AI Agent 在客服场景中的工程闭环：结构化意图路由、工具调用、业务数据库查询、轻量 RAG、会话管理和 Web/API 交互。

## 功能

- FastAPI 后端服务与 Swagger 文档
- 浏览器聊天页面
- 结构化 Router：输出 `intent`、`tool_name`、`slots`、`route_source`
- 商品查询、订单物流查询、售后 FAQ 查询工具
- RAG 检索：支持 Chroma 本地向量库，未构建索引时自动回退 TF-IDF 检索
- SQLite 会话管理与历史消息保存
- 用户注册/登录与按用户隔离的会话历史
- 售后工单：支持创建工单、查看工单和状态流转
- SQLAlchemy ORM 数据层，默认 SQLite，可通过 `DATABASE_URL` 切换数据库
- Alembic 数据库迁移，支持表结构版本化管理
- DeepSeek API 可选接入
- LLM 调用失败时自动回退到规则路由和模板回复

## 项目结构

```text
mvp_agent/
  app.py                 # FastAPI 路由和服务入口
  agent.py               # Router、工具调用、RAG 检索、DeepSeek 调用
  auth.py                # 密码哈希、Token 生成和用户认证
  db.py                  # SQLite 建表、seed 数据、会话和消息读写
  models.py              # SQLAlchemy ORM 模型
  vector_store.py        # Chroma 向量库索引构建和语义检索
  web.py                 # 浏览器聊天页面
  README.md              # 详细运行说明
  PROJECT_EVOLUTION.md   # 项目演进和面试讲法
  requirements.txt       # MVP 最小依赖
migrations/
  env.py                 # Alembic 迁移环境
  versions/              # 数据库迁移脚本
tools/
  build_chroma_index.py  # 将知识库 chunk 写入 Chroma 向量库
```

## 快速启动

```bash
pip install -r mvp_agent/requirements.txt
python -m mvp_agent.app
```

默认使用本地 SQLite。也可以通过 `DATABASE_URL` 切换数据库，例如：

```powershell
$env:DATABASE_URL="sqlite:///./mvp_agent/customer_agent.sqlite3"
```

数据库迁移：

```bash
alembic upgrade head
```

如果你已经用自动建表生成过本地 SQLite，迁移前可先删除本地运行库：

```powershell
Remove-Item .\mvp_agent\customer_agent.sqlite3
alembic upgrade head
python -m mvp_agent.app
```

访问：

```text
http://127.0.0.1:8010/chat
```

接口文档：

```text
http://127.0.0.1:8010/docs
```

## 示例问题

```text
推荐一款智能门锁
查一下订单 SO20260611001 的物流
智能门锁坏了怎么保修
智能门锁怎么安装
扫地机器人怎么维护
```

## Chroma 向量库

默认 RAG 会优先查询本地 Chroma 向量库。当前使用项目内置的轻量 embedding 函数写入 Chroma；如果还没有安装依赖或没有构建索引，会自动回退到 TF-IDF 检索，保证项目仍可运行。

构建向量索引：

```powershell
pip install chromadb
python tools/build_chroma_index.py
```

索引文件会保存在：

```text
mvp_agent/chroma_db/
```

该目录属于本地运行产物，不提交到 GitHub。

## 登录与会话隔离

浏览器页面支持游客模式，也支持注册/登录。登录后请求会携带 Bearer Token，后端会把聊天记录绑定到当前用户，左侧会话历史只展示自己的会话。

可用接口：

```text
POST /auth/register
POST /auth/login
GET /me
```

## 售后工单

登录用户可以把当前会话沉淀为售后工单，工单会关联当前用户和会话，支持后续状态流转。

可用接口：

```text
POST /tickets
GET /tickets
PATCH /tickets/{ticket_id}/status
```

## DeepSeek 接入

不设置 API Key 时，系统会使用规则路由和模板回复。设置环境变量后，会使用 DeepSeek 做结构化路由和回复生成。

PowerShell：

```powershell
$env:DEEPSEEK_API_KEY="your_api_key"
$env:DEEPSEEK_BASE_URL="https://api.deepseek.com"
$env:DEEPSEEK_MODEL="deepseek-chat"
python -m mvp_agent.app
```

请不要把 API Key 写入代码或提交到 GitHub。

## 当前定位

这是一个展示用的最小可运行闭环，不是完整企业级客服系统。后续可以继续扩展：

- MySQL/PostgreSQL
- Redis 缓存
- 人工客服后台
- LangGraph 多节点编排
- Docker Compose 部署
