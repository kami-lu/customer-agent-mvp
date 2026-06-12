from __future__ import annotations

CHAT_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>智能客服 Agent MVP</title>
  <style>
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f5f7fb;
      color: #172033;
    }
    main {
      max-width: 1180px;
      margin: 0 auto;
      min-height: 100vh;
      display: grid;
      grid-template-columns: 260px minmax(0, 1fr);
      grid-template-rows: auto 1fr auto;
      gap: 16px;
      padding: 24px;
      box-sizing: border-box;
    }
    header {
      grid-column: 1 / -1;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    h1 {
      margin: 0;
      font-size: 22px;
      font-weight: 700;
    }
    .status {
      font-size: 13px;
      color: #27745f;
      background: #e7f6ef;
      border: 1px solid #b9e4d2;
      padding: 6px 10px;
      border-radius: 999px;
    }
    #sidebar {
      grid-row: 2 / 4;
      background: white;
      border: 1px solid #dfe5ef;
      border-radius: 8px;
      padding: 12px;
      overflow: auto;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    }
    .sidebar-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 10px;
      font-size: 14px;
      font-weight: 700;
    }
    #new-chat {
      padding: 6px 9px;
      font-size: 12px;
      background: #e8edf5;
      color: #223047;
    }
    .conversation {
      width: 100%;
      display: block;
      text-align: left;
      margin-bottom: 8px;
      padding: 9px 10px;
      background: #f7f9fc;
      color: #223047;
      border: 1px solid #e1e7f0;
      border-radius: 6px;
    }
    .conversation.active {
      background: #e8f0ff;
      border-color: #9bbcff;
      color: #174ea6;
    }
    .conversation small {
      display: block;
      margin-top: 4px;
      color: #68758a;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    #messages {
      background: white;
      border: 1px solid #dfe5ef;
      border-radius: 8px;
      padding: 16px;
      overflow: auto;
      min-height: 420px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    }
    .msg {
      max-width: 78%;
      margin: 0 0 12px;
      padding: 10px 12px;
      border-radius: 8px;
      line-height: 1.55;
      white-space: pre-wrap;
    }
    .user {
      margin-left: auto;
      background: #2563eb;
      color: white;
    }
    .bot {
      background: #eef2f7;
      color: #172033;
    }
    .meta {
      margin-top: 8px;
      font-size: 12px;
      color: #607089;
    }
    form {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      background: white;
      border: 1px solid #dfe5ef;
      border-radius: 8px;
      padding: 10px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    }
    input {
      border: 0;
      outline: 0;
      font-size: 16px;
      padding: 10px;
      min-width: 0;
    }
    button {
      border: 0;
      border-radius: 6px;
      padding: 0 18px;
      background: #2563eb;
      color: white;
      font-size: 15px;
      cursor: pointer;
    }
    button:disabled {
      opacity: 0.55;
      cursor: wait;
    }
    .examples {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }
    .examples button {
      background: #e8edf5;
      color: #223047;
      padding: 7px 10px;
      font-size: 13px;
    }
    @media (max-width: 760px) {
      main {
        grid-template-columns: 1fr;
      }
      #sidebar {
        grid-row: auto;
        max-height: 180px;
      }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>智能客服 Agent MVP</h1>
      <span class="status">本地服务运行中</span>
    </header>
    <aside id="sidebar">
      <div class="sidebar-title">
        <span>会话历史</span>
        <button id="new-chat" type="button">新会话</button>
      </div>
      <div id="conversation-list"></div>
    </aside>
    <section id="messages">
      <div class="msg bot">亲，我是智能家居客服助手，可以帮您查询商品、订单、物流和售后问题。</div>
    </section>
    <section>
      <form id="chat-form">
        <input id="query" autocomplete="off" placeholder="输入问题，例如：推荐一款智能门锁" />
        <button id="send" type="submit">发送</button>
      </form>
      <div class="examples">
        <button type="button">推荐一款智能门锁</button>
        <button type="button">查一下订单 SO20260611001 的物流</button>
        <button type="button">智能门锁坏了怎么保修</button>
        <button type="button">智能门锁怎么安装</button>
      </div>
    </section>
  </main>
  <script>
    const form = document.querySelector("#chat-form");
    const input = document.querySelector("#query");
    const send = document.querySelector("#send");
    const messages = document.querySelector("#messages");
    const conversationList = document.querySelector("#conversation-list");
    const newChat = document.querySelector("#new-chat");
    let currentConversationId = `web-${Date.now()}`;

    function addMessage(text, kind, meta = "") {
      const item = document.createElement("div");
      item.className = `msg ${kind}`;
      item.textContent = text;
      if (meta) {
        const info = document.createElement("div");
        info.className = "meta";
        info.textContent = meta;
        item.appendChild(info);
      }
      messages.appendChild(item);
      messages.scrollTop = messages.scrollHeight;
    }

    function resetMessages() {
      messages.innerHTML = "";
      addMessage("亲，我是智能家居客服助手，可以帮您查询商品、订单、物流和售后问题。", "bot");
    }

    async function loadConversations() {
      const resp = await fetch("/conversations");
      const data = await resp.json();
      conversationList.innerHTML = "";
      data.conversations.forEach((conversation) => {
        const button = document.createElement("button");
        button.className = `conversation ${conversation.conversation_id === currentConversationId ? "active" : ""}`;
        button.type = "button";
        const title = document.createTextNode(conversation.title);
        const preview = document.createElement("small");
        preview.textContent = conversation.last_message || "暂无消息";
        button.appendChild(title);
        button.appendChild(preview);
        button.addEventListener("click", () => loadMessages(conversation.conversation_id));
        conversationList.appendChild(button);
      });
    }

    async function loadMessages(conversationId) {
      currentConversationId = conversationId;
      const resp = await fetch(`/conversations/${encodeURIComponent(conversationId)}/messages`);
      const data = await resp.json();
      messages.innerHTML = "";
      if (data.messages.length === 0) {
        resetMessages();
      } else {
        data.messages.forEach((message) => {
          addMessage(message.content, message.role === "user" ? "user" : "bot");
        });
      }
      await loadConversations();
    }

    async function ask(query) {
      addMessage(query, "user");
      input.value = "";
      send.disabled = true;
      try {
        const resp = await fetch("/chat", {
          method: "POST",
          headers: {"Content-Type": "application/json; charset=utf-8"},
          body: JSON.stringify({query, conversation_id: currentConversationId})
        });
        const data = await resp.json();
        currentConversationId = data.conversation_id || currentConversationId;
        const routeError = data.route_error ? ` | error: ${data.route_error}` : "";
        addMessage(
          data.answer || "接口没有返回 answer",
          "bot",
          `intent: ${data.intent || "-"} | tool: ${data.tool_name || "-"} | source: ${data.route_source || "-"} | ${data.route_reason || ""}${routeError}`
        );
        await loadConversations();
      } catch (error) {
        addMessage(`请求失败：${error.message}`, "bot");
      } finally {
        send.disabled = false;
        input.focus();
      }
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const query = input.value.trim();
      if (query) ask(query);
    });

    document.querySelectorAll(".examples button").forEach((button) => {
      button.addEventListener("click", () => ask(button.textContent));
    });

    newChat.addEventListener("click", async () => {
      currentConversationId = `web-${Date.now()}`;
      resetMessages();
      await loadConversations();
      input.focus();
    });

    loadConversations();
  </script>
</body>
</html>
"""
