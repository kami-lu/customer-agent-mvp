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
    .top-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      flex-wrap: wrap;
      gap: 10px;
    }
    .auth-panel {
      display: flex;
      align-items: center;
      gap: 6px;
      background: white;
      border: 1px solid #dfe5ef;
      border-radius: 8px;
      padding: 6px;
    }
    .auth-panel input {
      width: 110px;
      border: 1px solid #dfe5ef;
      border-radius: 6px;
      font-size: 13px;
      padding: 7px 8px;
    }
    .auth-panel button {
      padding: 7px 10px;
      font-size: 13px;
      background: #223047;
    }
    .auth-user {
      font-size: 13px;
      color: #43536b;
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
    .ticket-tools {
      margin-top: 16px;
      border-top: 1px solid #e1e7f0;
      padding-top: 12px;
    }
    #create-ticket {
      width: 100%;
      min-height: 34px;
      margin-bottom: 10px;
      background: #0f766e;
      font-size: 13px;
    }
    .ticket {
      margin-bottom: 8px;
      padding: 9px 10px;
      background: #f7f9fc;
      border: 1px solid #e1e7f0;
      border-radius: 6px;
      font-size: 13px;
    }
    .ticket strong {
      display: block;
      color: #223047;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .ticket small {
      display: block;
      color: #68758a;
      margin: 4px 0 7px;
    }
    .ticket-actions {
      display: flex;
      gap: 6px;
    }
    .ticket-actions button {
      flex: 1;
      min-height: 28px;
      padding: 0 6px;
      font-size: 12px;
      background: #e8edf5;
      color: #223047;
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
      <div class="top-actions">
        <span id="auth-user" class="auth-user">游客模式</span>
        <div class="auth-panel">
          <input id="username" autocomplete="username" placeholder="用户名" />
          <input id="password" autocomplete="current-password" type="password" placeholder="密码" />
          <button id="login" type="button">登录</button>
          <button id="register" type="button">注册</button>
          <button id="logout" type="button">退出</button>
        </div>
        <span class="status">本地服务运行中</span>
      </div>
    </header>
    <aside id="sidebar">
      <div class="sidebar-title">
        <span>会话历史</span>
        <button id="new-chat" type="button">新会话</button>
      </div>
      <div id="conversation-list"></div>
      <div class="ticket-tools">
        <div class="sidebar-title">
          <span>售后工单</span>
        </div>
        <button id="create-ticket" type="button">创建当前会话工单</button>
        <div id="ticket-list"></div>
      </div>
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
    const usernameInput = document.querySelector("#username");
    const passwordInput = document.querySelector("#password");
    const loginButton = document.querySelector("#login");
    const registerButton = document.querySelector("#register");
    const logoutButton = document.querySelector("#logout");
    const authUser = document.querySelector("#auth-user");
    const messages = document.querySelector("#messages");
    const conversationList = document.querySelector("#conversation-list");
    const ticketList = document.querySelector("#ticket-list");
    const newChat = document.querySelector("#new-chat");
    const createTicketButton = document.querySelector("#create-ticket");
    let currentConversationId = `web-${Date.now()}`;
    let authToken = localStorage.getItem("customer_agent_token") || "";

    function authHeaders(extra = {}) {
      const headers = {...extra};
      if (authToken) {
        headers.Authorization = `Bearer ${authToken}`;
      }
      return headers;
    }

    function setCurrentUser(user) {
      authUser.textContent = user ? `已登录：${user.username}` : "游客模式";
      logoutButton.style.display = user ? "inline-block" : "none";
    }

    async function authRequest(path) {
      const username = usernameInput.value.trim();
      const password = passwordInput.value;
      if (!username || !password) {
        addMessage("请先输入用户名和密码。", "bot");
        return;
      }
      const resp = await fetch(path, {
        method: "POST",
        headers: {"Content-Type": "application/json; charset=utf-8"},
        body: JSON.stringify({username, password})
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || "认证失败");
      }
      authToken = data.token;
      localStorage.setItem("customer_agent_token", authToken);
      setCurrentUser(data.user);
      currentConversationId = `web-${Date.now()}`;
      resetMessages();
      await loadConversations();
      await loadTickets();
    }

    async function restoreLogin() {
      if (!authToken) {
        setCurrentUser(null);
        return;
      }
      try {
        const resp = await fetch("/me", {headers: authHeaders()});
        if (!resp.ok) {
          throw new Error("token invalid");
        }
        const data = await resp.json();
        setCurrentUser(data.user);
      } catch (error) {
        authToken = "";
        localStorage.removeItem("customer_agent_token");
        setCurrentUser(null);
      }
    }

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
      const resp = await fetch("/conversations", {headers: authHeaders()});
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

    function ticketStatusText(status) {
      return {
        open: "待处理",
        processing: "处理中",
        resolved: "已解决",
        closed: "已关闭"
      }[status] || status;
    }

    async function loadTickets() {
      ticketList.innerHTML = "";
      if (!authToken) {
        ticketList.innerHTML = '<div class="ticket"><small>登录后可创建和查看工单</small></div>';
        return;
      }
      const resp = await fetch("/tickets", {headers: authHeaders()});
      const data = await resp.json();
      if (!resp.ok) {
        ticketList.innerHTML = '<div class="ticket"><small>工单加载失败</small></div>';
        return;
      }
      if (data.tickets.length === 0) {
        ticketList.innerHTML = '<div class="ticket"><small>暂无工单</small></div>';
        return;
      }
      data.tickets.forEach((ticket) => {
        const item = document.createElement("div");
        item.className = "ticket";
        const title = document.createElement("strong");
        title.textContent = `#${ticket.id} ${ticket.title}`;
        const meta = document.createElement("small");
        meta.textContent = `${ticketStatusText(ticket.status)} | ${ticket.description}`;
        const actions = document.createElement("div");
        actions.className = "ticket-actions";
        const processing = document.createElement("button");
        processing.type = "button";
        processing.textContent = "处理中";
        processing.addEventListener("click", () => updateTicketStatus(ticket.id, "processing"));
        const resolved = document.createElement("button");
        resolved.type = "button";
        resolved.textContent = "已解决";
        resolved.addEventListener("click", () => updateTicketStatus(ticket.id, "resolved"));
        actions.appendChild(processing);
        actions.appendChild(resolved);
        item.appendChild(title);
        item.appendChild(meta);
        item.appendChild(actions);
        ticketList.appendChild(item);
      });
    }

    async function updateTicketStatus(ticketId, status) {
      const resp = await fetch(`/tickets/${ticketId}/status`, {
        method: "PATCH",
        headers: authHeaders({"Content-Type": "application/json; charset=utf-8"}),
        body: JSON.stringify({status})
      });
      if (!resp.ok) {
        const data = await resp.json();
        addMessage(`工单状态更新失败：${data.detail || "未知错误"}`, "bot");
        return;
      }
      await loadTickets();
    }

    async function loadMessages(conversationId) {
      currentConversationId = conversationId;
      const resp = await fetch(`/conversations/${encodeURIComponent(conversationId)}/messages`, {headers: authHeaders()});
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
          headers: authHeaders({"Content-Type": "application/json; charset=utf-8"}),
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
        await loadTickets();
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
      await loadTickets();
      input.focus();
    });

    loginButton.addEventListener("click", async () => {
      try {
        await authRequest("/auth/login");
      } catch (error) {
        addMessage(`登录失败：${error.message}`, "bot");
      }
    });

    registerButton.addEventListener("click", async () => {
      try {
        await authRequest("/auth/register");
      } catch (error) {
        addMessage(`注册失败：${error.message}`, "bot");
      }
    });

    logoutButton.addEventListener("click", async () => {
      authToken = "";
      localStorage.removeItem("customer_agent_token");
      setCurrentUser(null);
      currentConversationId = `web-${Date.now()}`;
      resetMessages();
      await loadConversations();
      await loadTickets();
    });

    createTicketButton.addEventListener("click", async () => {
      if (!authToken) {
        addMessage("请先登录，再创建售后工单。", "bot");
        return;
      }
      const description = input.value.trim() || "用户需要人工客服继续处理当前会话中的售后问题";
      const resp = await fetch("/tickets", {
        method: "POST",
        headers: authHeaders({"Content-Type": "application/json; charset=utf-8"}),
        body: JSON.stringify({description, conversation_id: currentConversationId})
      });
      const data = await resp.json();
      if (!resp.ok) {
        addMessage(`创建工单失败：${data.detail || "未知错误"}`, "bot");
        return;
      }
      addMessage(`已创建售后工单 #${data.ticket.id}，状态：${ticketStatusText(data.ticket.status)}。`, "bot");
      await loadTickets();
    });

    restoreLogin().then(() => {
      loadConversations();
      loadTickets();
    });
  </script>
</body>
</html>
"""
