# 智能客服 Agent MVP 项目演进说明

这份文档用于记录当前项目从复杂客服 Agent 项目中抽取、复现、改造为可运行 MVP 的过程。面试或简历被追问时，可以按这里的顺序说明：我先跑通最小闭环，再逐步工程化，而不是一开始就堆复杂组件。

## 0. 项目定位

当前 `mvp_agent` 是一个智能家居电商客服 Agent 的最小可运行版本。

它覆盖的核心链路是：

```text
用户问题 -> 意图路由 -> 工具选择 -> SQLite 业务查询 -> 回复生成 -> 会话保存 -> Web/API 交互
```

这个版本的目标不是替代完整客服系统，而是把客服 Agent 最核心的工程闭环跑通，便于后续扩展到 FastAPI、数据库、RAG、LangGraph 和部署。

## 1. 从复杂项目中拆出最小闭环

### 做了什么

- 没有直接运行原始复杂项目。
- 单独新增 `mvp_agent/` 目录。
- 保留智能客服项目的核心思想：意图识别、工具调用、业务数据库查询、客服回复。
- 暂时去掉 MySQL、Redis、Neo4j、GraphRAG、登录系统、文件上传等重依赖。

### 为什么这么做

原项目依赖较多，完整运行需要数据库、缓存、图数据库、大模型服务和前端静态包。如果直接复现，容易被环境问题卡住，也不利于面试时讲清楚每个模块。

先做 MVP 的好处是：

- 能快速得到真实可运行结果。
- 每个模块都能解释清楚。
- 后续可以逐步替换和扩展，而不是一次性引入所有复杂组件。

### 面试怎么讲

可以说：

```text
我先没有直接堆完整技术栈，而是把客服 Agent 抽象成最小闭环：路由、工具、数据库、回复和会话存储。这样可以先验证业务流程，再逐步工程化扩展。
```

## 2. 使用 SQLite 构建本地业务数据

### 做了什么

在 `mvp_agent/app.py` 中使用 SQLite 自动创建四张表：

- `products`：商品数据
- `orders`：订单和物流数据
- `faqs`：售后、发票、安装等 FAQ
- `messages`：会话消息记录

启动时会自动初始化示例数据，包括智能门锁、智能灯带、扫地机器人、智能网关，以及两个示例订单。

### 为什么这么做

完整客服系统通常需要 MySQL 或 PostgreSQL，但 MVP 阶段使用 SQLite 更轻量：

- 不需要额外安装数据库服务。
- 面试演示时更稳定。
- 仍然能体现数据库建模、查询和会话落库能力。
- 后续迁移到 MySQL/PostgreSQL 时表结构和业务逻辑可以复用。

### 面试怎么讲

可以说：

```text
我先用 SQLite 做本地业务库，模拟商品、订单、FAQ 和消息表。这样既能演示数据库查询和会话落库，也避免早期被数据库部署卡住。后续可以平滑替换为 MySQL 或 PostgreSQL。
```

## 3. 实现规则版意图路由

### 做了什么

实现 `route_query()`，把用户问题分成四类：

- `product`：商品咨询
- `order`：订单或物流查询
- `after_sales`：售后、退换、保修
- `general`：普通问题

示例：

```text
推荐一款智能门锁 -> product
查一下订单 SO20260611001 的物流 -> order
智能门锁坏了怎么保修 -> after_sales
你能做什么 -> general
```

### 为什么这么做

真实 Agent 可以用 LLM 做意图识别，但早期用规则路由更可控：

- 方便验证整体链路。
- 不依赖 API Key。
- 输出稳定，方便调试。
- 后续可以替换为 LLM 结构化输出。

### 面试怎么讲

可以说：

```text
MVP 阶段我先用关键词规则做 Router，保证链路可控；后续计划用 LLM 输出 JSON，包括 intent、slots 和 tool_name，再根据结构化结果调用工具。
```

## 4. 实现工具调用

### 做了什么

根据不同意图调用不同工具函数：

- `search_products()`：查询商品信息
- `search_order()`：查询订单和物流状态
- `search_faq()`：查询售后政策

工具查询结果会放到 `tool_context` 中，再交给回复生成模块。

### 为什么这么做

客服 Agent 不能只靠模型自由生成，尤其是库存、价格、订单状态这类事实信息必须来自数据库。

这样设计的好处是：

- 减少幻觉。
- 数据来源可追踪。
- 工具边界清晰。
- 后续方便接入真实商品库、订单系统或工单系统。

### 面试怎么讲

可以说：

```text
我把商品、订单、售后都封装成工具函数，Agent 先判断意图，再调用对应工具。价格、库存、物流这些事实不让模型编，而是从数据库查出来。
```

## 5. 实现回复生成

### 做了什么

当前支持两种回复方式：

1. 没有 `DEEPSEEK_API_KEY` 时，使用规则模板生成回复。
2. 设置 `DEEPSEEK_API_KEY` 后，调用 DeepSeek，基于工具查询结果生成更自然的客服回复。

### 为什么这么做

这样既能保证项目离线可演示，也能保留真实 LLM 接入能力：

- 无 API Key 时也能跑完整链路。
- 有 API Key 时可以提升回复自然度。
- LLM 只基于 `tool_context` 回答，降低编造风险。

### 面试怎么讲

可以说：

```text
我做了模板兜底和 LLM 增强两种模式。模板保证系统稳定可用，LLM 负责自然语言表达，但核心事实仍然来自工具查询结果。
```

## 6. 增加会话落库

### 做了什么

每次调用 `run_agent()` 时，会把用户问题和助手回复写入 `messages` 表。

保存字段包括：

- `conversation_id`
- `role`
- `content`
- `created_at`

### 为什么这么做

客服系统需要记录会话历史，后续才能支持：

- 会话列表
- 历史消息查看
- 多轮上下文
- 用户行为分析
- 人工客服接管

### 面试怎么讲

可以说：

```text
我没有只做一次性问答，而是把每轮 user/assistant 消息都保存下来，为后续多轮对话、上下文记忆和客服工单分析做准备。
```

## 7. 增加浏览器聊天页面

### 做了什么

在 `CHAT_HTML` 中实现了一个简单 Web 页面，包含：

- 聊天展示区
- 输入框
- 发送按钮
- 示例问题按钮
- 显示 `intent` 和路由原因

浏览器可访问：

```text
http://127.0.0.1:8010/chat
```

### 为什么这么做

只提供 API 不利于展示。加一个简单网页后，面试或录屏时可以直接演示：

- 用户输入问题
- 系统返回客服回复
- 页面展示意图识别结果

### 面试怎么讲

可以说：

```text
我加了一个轻量 Web 页面，方便直接演示 Agent 从用户输入到工具查询再到回复生成的完整过程。
```

## 8. 从标准库 HTTP 服务升级到 FastAPI

### 做了什么

最初版本用 Python 标准库 `http.server` 提供接口。之后改为 FastAPI：

- `GET /`：返回聊天页面
- `GET /chat`：返回聊天页面
- `POST /chat`：调用 Agent 并返回 JSON
- `GET /health`：健康检查
- `GET /docs`：自动生成 Swagger 文档

新增最小依赖文件：

```text
mvp_agent/requirements.txt
```

内容：

```text
fastapi>=0.110.0
uvicorn>=0.27.0
```

### 为什么这么做

FastAPI 更适合真实工程：

- 自动生成接口文档。
- 支持 Pydantic 请求校验。
- 后续容易扩展鉴权、路由分层、中间件、异步任务。
- 更接近真实后端服务开发方式。

### 面试怎么讲

可以说：

```text
我先用标准库快速验证链路，确认 Agent 逻辑没问题后，再迁移到 FastAPI。这样既保证了迭代速度，也让项目结构更接近真实后端服务。
```

## 9. 增加会话列表和历史消息接口

### 做了什么

在原有 `messages` 表的基础上新增 `conversations` 表，用来记录每个会话的标题、创建时间和更新时间。

新增接口：

```text
GET /conversations
GET /conversations/{conversation_id}/messages
```

同时升级 Web 页面：

- 左侧展示会话历史。
- 支持点击历史会话加载消息。
- 支持创建新会话。
- 每次发送消息后自动刷新会话列表。

### 为什么这么做

真实客服系统不是一次性问答，而是围绕“会话”工作的。客服需要看到用户过去问了什么、系统怎么回答、当前会话是否需要继续处理。

增加会话管理后，项目从“单次问答 Demo”变成了更接近真实客服工作台的形态：

- 可以按会话组织消息。
- 支持历史记录查看。
- 为后续用户登录、多轮上下文、人工接管和工单系统打基础。

### 面试怎么讲

可以说：

```text
我在消息表之外补了 conversations 表，用于维护会话级元数据；然后提供会话列表和消息详情接口，前端左侧可以加载历史会话。这一步让系统从一次性 API 问答升级为有会话管理能力的客服系统。
```

## 10. 升级为结构化 Router

### 做了什么

将原来的简单路由结果：

```text
intent + reason
```

升级为结构化路由结果：

```text
intent + tool_name + slots + reason + source
```

字段含义：

- `intent`：用户意图，如 `product`、`order`、`after_sales`、`general`
- `tool_name`：后续要调用的工具，如 `search_products`、`search_order`、`search_faq`
- `slots`：从用户问题中抽取出的槽位，如订单号、商品关键词、售后关键词
- `reason`：路由理由
- `source`：路由来源，`rule` 表示规则兜底，`llm` 表示 DeepSeek 路由

当前支持两种路由方式：

1. 无 API Key 时使用规则路由，保证本地可运行。
2. 设置 `DEEPSEEK_API_KEY` 后，调用 DeepSeek 进行 JSON 格式的结构化意图识别。

DeepSeek 请求层使用 `requests` 统一发送 `/v1/chat/completions` 请求，并在失败时把错误写入 `route_error`，方便排查 API Key、余额、网络和 SSL 问题。

### 为什么这么做

真实 Agent 不能只判断一个粗粒度意图，还需要知道下一步调用哪个工具，以及工具需要哪些参数。

例如：

```text
查一下订单 SO20260611001 的物流
```

路由结果应包含：

```json
{
  "intent": "order",
  "tool_name": "search_order",
  "slots": {"order_id": "SO20260611001"}
}
```

这样 Tool Executor 就不需要重新理解用户问题，而是可以直接根据结构化结果执行查询。

### 面试怎么讲

可以说：

```text
我把 Router 从简单的 intent 分类升级成结构化输出，包含 intent、tool_name 和 slots。这样 Agent 不只是判断问题类型，还能明确下一步调用哪个工具、传什么参数。没有 API Key 时走规则兜底，有 DeepSeek Key 时可以切换成 LLM JSON 路由。
```

注意：API Key 只通过环境变量配置，不写入代码仓库，也不要在截图中暴露。

## 11. 增加轻量 RAG 知识库

### 做了什么

新增 `knowledge_chunks` 表，用来存储客服知识库片段，包括：

- 智能门锁安装说明
- 智能门锁保修政策
- 智能灯带使用说明
- 扫地机器人维护说明
- 退货与发票规则

新增 `search_knowledge` 工具：

- 对用户问题和知识库 chunk 做 tokenize。
- 使用 TF-IDF 加余弦相似度计算相关性。
- 返回 top chunks、来源文件和相似度分数。

Router 增加 `rag` 意图：

```text
智能门锁怎么安装 -> rag -> search_knowledge
扫地机器人怎么维护 -> rag -> search_knowledge
```

### 为什么这么做

完整 RAG 通常会使用 embedding 模型和向量数据库，但早期 MVP 阶段先用轻量本地检索更合适：

- 不需要额外部署 Chroma、Milvus、Weaviate。
- 不依赖 embedding API。
- 检索逻辑透明，面试时容易解释。
- 后续可以把 `search_knowledge` 内部实现替换成向量检索，而不影响上层 Agent 流程。

后续迭代中已经将该检索层升级为 Chroma 向量检索优先，并保留 TF-IDF 作为兜底。

### 面试怎么讲

可以说：

```text
我先实现了一个轻量 RAG：把售后和产品说明切成 knowledge_chunks，用 TF-IDF + 余弦相似度做本地检索，返回 top chunks 给回复生成模块。这样先跑通知识库问答链路，再把检索层平滑升级为 Chroma 向量检索，而不影响上层 Agent 流程。
```

## 12. 模块化拆分

### 做了什么

最初为了快速验证，MVP 的页面、数据库、Agent、RAG 和 FastAPI 路由都写在 `app.py` 中。随着功能增加，单文件已经不利于维护，因此拆分为：

```text
mvp_agent/
  app.py      # FastAPI 路由和服务入口
  agent.py    # Router、工具调用、RAG 检索、DeepSeek 调用
  db.py       # SQLite 建表、seed 数据、会话和消息读写
  web.py      # 浏览器聊天页面
```

### 为什么这么做

单文件适合早期验证，但不适合继续扩展。拆分后每个模块职责更清楚：

- `app.py` 只关心 HTTP API。
- `agent.py` 只关心 Agent 决策和工具编排。
- `db.py` 只关心数据持久化。
- `web.py` 只关心前端页面。

这样后续增加登录、向量库、测试和部署时，不会把所有逻辑继续堆进一个文件。

### 面试怎么讲

可以说：

```text
我前期为了快速验证闭环，把逻辑集中在单文件里；当功能扩展到会话管理、结构化路由和 RAG 后，我做了模块化拆分，把 FastAPI 路由、Agent 逻辑、数据库层和页面层分开，提高可维护性。
```

## 13. 数据库层升级为 SQLAlchemy ORM

### 做了什么

将原来的 `sqlite3` 手写 SQL 数据层升级为 SQLAlchemy ORM。

新增：

```text
mvp_agent/models.py
```

抽象出这些模型：

- `Product`
- `Order`
- `FAQ`
- `KnowledgeChunk`
- `Conversation`
- `Message`

`db.py` 现在负责：

- 创建 `engine`
- 创建 `SessionLocal`
- 初始化表结构
- seed 示例数据
- 会话和消息读写

默认仍然使用本地 SQLite，同时支持通过 `DATABASE_URL` 切换数据库。

### 为什么这么做

最初使用 `sqlite3` 是为了快速验证 MVP 闭环，但随着功能增加，手写 SQL 的维护成本会升高。

升级 ORM 后的好处：

- 表结构由模型表达，更清晰。
- 查询逻辑更接近真实后端工程。
- 后续增加用户、工单、知识库版本等表更方便。
- 可以通过 `DATABASE_URL` 平滑迁移到 MySQL/PostgreSQL。
- 为后续接 Alembic 数据库迁移做准备。

### 面试怎么讲

可以说：

```text
我最初用 sqlite3 手写 SQL 快速跑通 Agent 闭环；后续为了提升工程可维护性，将数据层升级为 SQLAlchemy ORM，抽象 Product、Order、FAQ、KnowledgeChunk、Conversation、Message 等模型，并通过 DATABASE_URL 支持后续迁移到 MySQL 或 PostgreSQL。
```

## 14. 增加 Alembic 数据库迁移

### 做了什么

新增 Alembic 迁移配置：

```text
alembic.ini
migrations/env.py
migrations/script.py.mako
migrations/versions/0001_initial_schema.py
```

初始迁移脚本负责创建：

- `products`
- `orders`
- `faqs`
- `knowledge_chunks`
- `conversations`
- `messages`

迁移环境会读取 `DATABASE_URL`，默认使用本地 SQLite，也可以切换到 MySQL/PostgreSQL。

### 为什么这么做

`Base.metadata.create_all()` 适合 MVP 演示，但真实项目需要记录每次表结构变更，否则多人协作和线上升级很难管理。

引入 Alembic 后：

- 表结构变更可以版本化。
- 每次数据库升级都有 migration 文件。
- 后续添加用户表、工单表、知识库版本表时，可以通过迁移脚本管理。
- 更接近真实后端工程流程。

### 怎么运行

```bash
alembic upgrade head
```

如果本地已经存在自动建表生成的 SQLite 文件，可以先删除运行库再执行迁移：

```powershell
Remove-Item .\mvp_agent\customer_agent.sqlite3
alembic upgrade head
python -m mvp_agent.app
```

### 面试怎么讲

可以说：

```text
在 ORM 层稳定后，我继续接入 Alembic，把表结构从 create_all 的自动建表升级为 migration 版本管理。这样后续新增用户、工单、知识库版本等表时，可以通过迁移脚本可控升级，也为团队协作和线上部署做准备。
```

## 15. 清理项目并脱敏

### 做了什么

整理项目时删除或忽略了：

- `.venv`
- `__pycache__`
- 日志文件
- 上传文件
- 本地 `.env`
- PDF 项目说明书
- SQLite 运行库
- 第三方大包和压缩产物

同时将 `.env.example` 中的真实样式密码替换为占位符。

### 为什么这么做

代码仓库发给别人前必须清理运行产物和敏感信息，否则会显得不专业，也可能泄露本地配置。

### 面试怎么讲

可以说：

```text
我整理仓库时把虚拟环境、日志、上传文件、本地 .env 和运行数据库都清理掉，只保留源码、依赖说明和示例配置，保证项目可复现且不泄露敏感信息。
```

## 16. 当前项目能演示什么

### 推荐演示问题

```text
推荐一款智能门锁
查一下订单 SO20260611001 的物流
智能门锁坏了怎么保修
你能做什么
```

### 可展示的能力

- Web 聊天界面
- 左侧会话历史
- FastAPI 接口
- Swagger 文档
- 结构化意图路由
- 工具调用
- slots 槽位抽取
- SQLite 查询
- Chroma / TF-IDF RAG 知识库检索
- 检索来源和相似度分数
- 模块化代码结构
- SQLAlchemy ORM 数据层
- Alembic 数据库迁移
- 模板/LLM 双模式回复
- 会话记录保存与历史消息查询

## 17. 增加用户登录和会话隔离

### 做了什么

新增了用户与认证能力：

- `User` 用户表
- `AuthToken` 登录 Token 表
- 密码 PBKDF2 哈希存储
- `/auth/register` 注册接口
- `/auth/login` 登录接口
- `/me` 当前用户接口
- `conversations.user_id` 字段
- Web 页面登录/注册/退出入口
- 登录用户只读取自己的会话历史

### 为什么这么做

原来的版本所有会话都在同一个列表里，适合单机演示，但不像真实客服系统。加入用户体系后，聊天记录可以按用户隔离，后续也能继续扩展会员信息、工单、订单权限校验和后台客服接管。

### 面试怎么讲

可以说：

```text
我在会话系统上继续补了用户认证能力：用户注册时使用 PBKDF2 对密码做加盐哈希，登录后生成服务端 Token，前端通过 Authorization Bearer Token 调用接口。后端根据 Token 解析 user_id，并在查询会话和消息时按 user_id 过滤，保证不同用户只能看到自己的历史记录。这个改动让 MVP 从单用户演示升级为更接近真实客服系统的多用户会话模型。
```

## 18. 增加售后工单和人工接管入口

### 做了什么

新增了工单闭环：

- `Ticket` 工单表
- `/tickets` 创建工单接口
- `/tickets` 工单列表接口
- `/tickets/{ticket_id}/status` 状态更新接口
- 工单关联 `user_id` 和 `conversation_id`
- Web 页面支持创建当前会话工单
- Web 页面支持查看自己的工单列表
- 工单状态支持 `open`、`processing`、`resolved`、`closed`

### 为什么这么做

只做问答的客服 Agent 仍然偏 Demo。真实客服系统里，很多售后问题需要人工处理、跨天跟进或状态流转，所以需要把一次对话沉淀成可追踪的工单。这个改动让系统从“能回答问题”进一步变成“能承接业务流程”。

### 面试怎么讲

可以说：

```text
在登录和会话隔离之后，我继续补了售后工单闭环。用户登录后可以基于当前会话创建工单，工单表关联 user_id 和 conversation_id，后续可以查看自己的工单并进行 open、processing、resolved、closed 的状态流转。这样 Agent 无法直接解决或需要人工跟进的问题可以沉淀为业务对象，为后续人工客服接管、后台处理和消息通知做准备。
```

## 19. 增加 Chroma 向量数据库

### 做了什么

新增了向量检索能力：

- `vector_store.py` 封装 Chroma 本地持久化向量库
- `tools/build_chroma_index.py` 将 SQLite 中的知识库 chunk 写入 Chroma
- RAG 查询优先走 Chroma 本地向量检索
- Chroma 不可用或索引为空时自动回退 TF-IDF
- `mvp_agent/chroma_db/` 作为本地索引目录并加入 `.gitignore`

### 为什么这么做

早期 TF-IDF 检索依赖关键词重合，适合小知识库演示，但面对更口语化的问题时召回能力不足。引入 Chroma 后，可以把知识库 chunk 持久化为向量索引；同时保留 TF-IDF 兜底，避免向量库依赖或索引未构建导致项目跑不起来。当前版本使用轻量本地 embedding 函数，后续可替换为 sentence-transformers 或云端 embedding 模型。

### 面试怎么讲

可以说：

```text
我将 RAG 检索层从 TF-IDF 轻量检索升级为 Chroma 向量数据库优先召回，并保留 TF-IDF 兜底。知识库 chunk 仍存放在 SQLite 中，构建索引脚本会读取 chunk 并写入本地 Chroma 持久化目录。查询时 Agent 先走 Chroma 向量检索，若 Chroma 不可用或索引为空，再自动回退到 TF-IDF，兼顾召回能力和项目可复现性。
```

## 20. 当前项目还没有做什么

当前 MVP 暂未实现：

- 多轮上下文理解
- MySQL/PostgreSQL
- Redis 缓存
- 完整人工客服后台
- Neo4j 图谱查询
- LangGraph 节点编排
- Docker 部署
- 公网部署

这些不是缺陷，而是后续迭代方向。

## 21. 后续迭代路线

建议按这个顺序继续做：

1. 继续拆分为更细的目录：`api/`、`tools/`、`services/`。
2. 接入 MySQL 或 PostgreSQL。
3. 增加人工客服后台和工单分配。
4. 将本地 Chroma 进一步升级为可部署的向量服务或混合检索。
5. 引入 LangGraph 编排 Agent 节点。
6. 使用 Docker Compose 部署。

## 22. 简历表述建议

可以写：

```text
实现智能家居电商客服 Agent MVP，基于 FastAPI + SQLAlchemy + SQLite 构建可运行的客服问答闭环，并通过 DATABASE_URL 预留 MySQL/PostgreSQL 迁移能力；接入 Alembic 管理数据库 schema 版本；按 FastAPI 路由、Agent 编排、认证、数据库层和 Web 页面进行模块化拆分；设计结构化 Router，输出 intent、tool_name、slots 和路由来源，支持商品咨询、订单物流、售后 FAQ 与知识库问答；封装商品查询、订单查询、售后查询和 RAG 检索工具，支持 Chroma 向量检索优先与 TF-IDF 兜底；实现用户注册登录、Token 认证和按用户隔离的会话历史；新增售后工单闭环，支持用户基于会话创建工单、查看工单和状态流转；提供 Web 聊天页面与 Swagger 接口文档；支持无 API Key 的规则兜底和 DeepSeek API 结构化路由/回复增强。
```

不要写：

```text
独立完成大型企业级客服 Agent 系统
完整实现 GraphRAG / Neo4j / Redis / 多 Agent 并行
已上线生产环境
```

除非这些能力后续真的实现并跑通。
