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

完整 RAG 通常会使用 embedding 模型和向量数据库，但 MVP 阶段先用轻量本地检索更合适：

- 不需要额外部署 Chroma、Milvus、Weaviate。
- 不依赖 embedding API。
- 检索逻辑透明，面试时容易解释。
- 后续可以把 `search_knowledge` 内部实现替换成向量检索，而不影响上层 Agent 流程。

### 面试怎么讲

可以说：

```text
我先实现了一个轻量 RAG：把售后和产品说明切成 knowledge_chunks，用 TF-IDF + 余弦相似度做本地检索，返回 top chunks 给回复生成模块。这样先跑通知识库问答链路，后续可以平滑替换为 embedding + 向量数据库。
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

## 14. 清理项目并脱敏

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

## 15. 当前项目能演示什么

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
- 轻量 RAG 知识库检索
- 检索来源和相似度分数
- 模块化代码结构
- SQLAlchemy ORM 数据层
- 模板/LLM 双模式回复
- 会话记录保存与历史消息查询

## 16. 当前项目还没有做什么

当前 MVP 暂未实现：

- 用户登录注册
- 多轮上下文理解
- MySQL/PostgreSQL
- Redis 缓存
- Neo4j 图谱查询
- embedding 向量化和向量数据库
- Alembic 数据库迁移
- LangGraph 节点编排
- Docker 部署
- 公网部署

这些不是缺陷，而是后续迭代方向。

## 17. 后续迭代路线

建议按这个顺序继续做：

1. 继续拆分为更细的目录：`api/`、`tools/`、`services/`。
2. 接入 MySQL 或 PostgreSQL。
3. 增加 Alembic 数据库迁移。
4. 增加登录注册。
5. 将轻量 RAG 替换为 embedding + 向量数据库。
6. 引入 LangGraph 编排 Agent 节点。
7. 使用 Docker Compose 部署。

## 18. 简历表述建议

可以写：

```text
实现智能家居电商客服 Agent MVP，基于 FastAPI + SQLAlchemy + SQLite 构建可运行的客服问答闭环，并通过 DATABASE_URL 预留 MySQL/PostgreSQL 迁移能力；按 FastAPI 路由、Agent 编排、数据库层和 Web 页面进行模块化拆分；设计结构化 Router，输出 intent、tool_name、slots 和路由来源，支持商品咨询、订单物流、售后 FAQ 与知识库问答；封装商品查询、订单查询、售后查询和轻量 RAG 检索工具，基于工具结果生成客服回复并保存会话记录；新增会话列表和历史消息查询接口，提供 Web 聊天页面与 Swagger 接口文档；支持无 API Key 的规则兜底和 DeepSeek API 结构化路由/回复增强。
```

不要写：

```text
独立完成大型企业级客服 Agent 系统
完整实现 GraphRAG / Neo4j / Redis / 多 Agent 并行
已上线生产环境
```

除非这些能力后续真的实现并跑通。
