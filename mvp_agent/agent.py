from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

import requests
from sqlalchemy import case, or_, select

from .db import get_session, make_conversation_title, model_to_dict, save_message, upsert_conversation
from .models import FAQ, KnowledgeChunk, Order, Product
from .vector_store import VectorStoreUnavailable, search_chroma


@dataclass
class RouteResult:
    intent: str
    tool_name: str
    slots: dict[str, Any]
    reason: str
    source: str = "rule"
    error: str = ""


def extract_order_id(query: str) -> str:
    words = query.replace("，", " ").replace(",", " ").split()
    return next((word.upper() for word in words if word.upper().startswith("SO")), "")


def rule_route_query(query: str) -> RouteResult:
    text = query.lower()
    if any(word in text for word in ["订单", "物流", "快递", "so2026", "发货"]):
        return RouteResult(
            intent="order",
            tool_name="search_order",
            slots={"order_id": extract_order_id(query)},
            reason="用户在查询订单或物流状态",
        )
    if any(word in text for word in ["说明", "怎么用", "如何使用", "配网", "安装", "维护", "保养", "手册"]):
        return RouteResult(
            intent="rag",
            tool_name="search_knowledge",
            slots={"query": query},
            reason="用户在咨询知识库文档类问题",
        )
    if any(word in text for word in ["退", "换", "保修", "售后", "坏了", "维修", "发票"]):
        return RouteResult(
            intent="after_sales",
            tool_name="search_faq",
            slots={"keyword": next((word for word in ["退货", "换货", "保修", "售后", "维修"] if word in query), "")},
            reason="用户在咨询售后政策或处理方式",
        )
    if any(word in text for word in ["推荐", "价格", "库存", "门锁", "灯", "机器人", "网关", "商品"]):
        keywords = product_keywords(query)
        return RouteResult(
            intent="product",
            tool_name="search_products",
            slots={"keywords": keywords},
            reason="用户在咨询商品信息",
        )
    return RouteResult(
        intent="general",
        tool_name="none",
        slots={},
        reason="用户问题不需要查询业务数据库",
    )


def parse_json_object(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("router response is not a JSON object")
    return parsed


def deepseek_chat_completion(payload: dict[str, Any]) -> dict[str, Any]:
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"
    url = f"{base_url}/chat/completions"
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text[:300]}")
    return response.json()


def call_deepseek_router(query: str) -> RouteResult | None:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        return None

    schema_instruction = {
        "intent": "product|order|after_sales|rag|general",
        "tool_name": "search_products|search_order|search_faq|search_knowledge|none",
        "slots": {
            "keywords": "商品关键词列表，可为空",
            "order_id": "订单号，可为空",
            "keyword": "售后 FAQ 关键词，可为空",
        },
        "reason": "一句中文分类理由",
    }
    payload = {
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是电商客服 Agent 的 Router。只输出 JSON，不要输出 Markdown。"
                    "根据用户问题选择意图和工具。可用工具："
                    "search_products 查询商品，search_order 查询订单物流，"
                    "search_faq 查询售后 FAQ，search_knowledge 查询知识库文档，"
                    "none 表示无需工具。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"question": query, "schema": schema_instruction},
                    ensure_ascii=False,
                ),
            },
        ],
        "temperature": 0,
    }
    try:
        result = deepseek_chat_completion(payload)
        raw_content = result["choices"][0]["message"]["content"].strip()
        route_data = parse_json_object(raw_content)
        intent = str(route_data.get("intent", "general"))
        if intent not in {"product", "order", "after_sales", "rag", "general"}:
            raise ValueError(f"invalid intent: {intent}")
        default_tool = {
            "product": "search_products",
            "order": "search_order",
            "after_sales": "search_faq",
            "rag": "search_knowledge",
            "general": "none",
        }[intent]
        slots = route_data.get("slots")
        return RouteResult(
            intent=intent,
            tool_name=str(route_data.get("tool_name") or default_tool),
            slots=slots if isinstance(slots, dict) else {},
            reason=str(route_data.get("reason") or "LLM 路由完成"),
            source="llm",
        )
    except (requests.RequestException, RuntimeError, KeyError, TimeoutError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return RouteResult(
            intent="general",
            tool_name="none",
            slots={},
            reason="DeepSeek 路由失败，已回退规则路由",
            source="llm_error",
            error=str(exc)[:300],
        )


def route_query(query: str) -> RouteResult:
    llm_route = call_deepseek_router(query)
    if llm_route and llm_route.source == "llm":
        return llm_route
    rule_route = rule_route_query(query)
    if llm_route and llm_route.error:
        rule_route.error = llm_route.error
    return rule_route


def product_keywords(query: str) -> list[str]:
    candidates = ["门锁", "灯带", "灯", "机器人", "扫地", "网关", "安防", "照明", "清洁", "控制"]
    keywords = [word for word in candidates if word in query]
    return keywords or [query]


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    latin_tokens = re.findall(r"[a-z0-9]+", lowered)
    cjk_tokens = re.findall(r"[\u4e00-\u9fff]{1,2}", lowered)
    return latin_tokens + cjk_tokens


def cosine_similarity(query_tokens: list[str], doc_tokens: list[str], doc_count: int, doc_freq: Counter[str]) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    query_tf = Counter(query_tokens)
    doc_tf = Counter(doc_tokens)
    shared = set(query_tf) & set(doc_tf)
    score = 0.0
    for token in shared:
        idf = math.log((doc_count + 1) / (doc_freq[token] + 1)) + 1
        score += query_tf[token] * doc_tf[token] * idf * idf
    query_norm = math.sqrt(
        sum((count * (math.log((doc_count + 1) / (doc_freq[token] + 1)) + 1)) ** 2 for token, count in query_tf.items())
    )
    doc_norm = math.sqrt(
        sum((count * (math.log((doc_count + 1) / (doc_freq[token] + 1)) + 1)) ** 2 for token, count in doc_tf.items())
    )
    if query_norm == 0 or doc_norm == 0:
        return 0.0
    return score / (query_norm * doc_norm)


def search_knowledge_tfidf(query: str, limit: int = 3) -> list[dict[str, Any]]:
    with get_session() as session:
        chunks = session.scalars(select(KnowledgeChunk)).all()
        documents = [model_to_dict(chunk, ["id", "title", "content", "source"]) for chunk in chunks]
    tokenized_docs = [tokenize(f"{doc['title']} {doc['content']}") for doc in documents]
    doc_freq: Counter[str] = Counter()
    for tokens in tokenized_docs:
        doc_freq.update(set(tokens))
    query_tokens = tokenize(query)
    scored: list[dict[str, Any]] = []
    for doc, tokens in zip(documents, tokenized_docs):
        score = cosine_similarity(query_tokens, tokens, len(documents), doc_freq)
        if score > 0:
            scored.append({**doc, "score": round(score, 4), "retrieval": "tfidf"})
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:limit]


def search_knowledge(query: str, limit: int = 3) -> list[dict[str, Any]]:
    try:
        vector_results = search_chroma(query, limit)
        if vector_results:
            return vector_results
    except (VectorStoreUnavailable, Exception):
        pass
    return search_knowledge_tfidf(query, limit)


def search_products(query: str, keywords: list[str] | None = None) -> list[dict[str, Any]]:
    keywords = keywords or product_keywords(query)
    with get_session() as session:
        products: list[Product] = []
        for keyword in keywords:
            pattern = f"%{keyword}%"
            products = session.scalars(
                select(Product)
                .where(
                    or_(
                        Product.name.like(pattern),
                        Product.category.like(pattern),
                        Product.description.like(pattern),
                    )
                )
                .order_by(
                    case(
                        (Product.name.like(pattern), 1),
                        (Product.category.like(pattern), 2),
                        else_=3,
                    ),
                    Product.stock.desc(),
                )
                .limit(3)
            ).all()
            if products:
                break
        if not products:
            products = session.scalars(select(Product).order_by(Product.stock.desc()).limit(3)).all()
        return [model_to_dict(product, ["name", "category", "price", "stock", "description"]) for product in products]


def search_order(query: str, order_id: str = "") -> dict[str, Any] | None:
    order_id = order_id or extract_order_id(query)
    with get_session() as session:
        if order_id:
            order = session.get(Order, order_id)
        else:
            order = session.scalars(select(Order).order_by(Order.id.desc()).limit(1)).first()
        return model_to_dict(order, ["id", "status", "logistics", "after_sales"]) if order else None


def search_faq(query: str, keyword: str = "") -> str:
    with get_session() as session:
        faqs = session.scalars(select(FAQ)).all()
    if keyword:
        for faq in faqs:
            if faq.keyword == keyword or faq.keyword in keyword:
                return faq.answer
    for faq in faqs:
        if faq.keyword in query:
            return faq.answer
    return "售后问题我可以帮您先登记，建议提供订单号、商品名称和问题现象。"


def build_context(route: RouteResult, query: str) -> dict[str, Any]:
    if route.intent == "product":
        keywords = route.slots.get("keywords")
        if isinstance(keywords, str):
            keywords = [keywords]
        return {"products": search_products(query, keywords if isinstance(keywords, list) else None)}
    if route.intent == "order":
        return {"order": search_order(query, str(route.slots.get("order_id") or ""))}
    if route.intent == "after_sales":
        return {"policy": search_faq(query, str(route.slots.get("keyword") or ""))}
    if route.intent == "rag":
        return {"chunks": search_knowledge(str(route.slots.get("query") or query))}
    return {"note": "general response"}


def fallback_response(intent: str, context: dict[str, Any]) -> str:
    if intent == "product":
        products = context["products"]
        lines = [
            f"{item['name']}：{item['price']} 元，库存 {item['stock']} 件，{item['description']}"
            for item in products
        ]
        return "亲，给您查到这些商品：\n" + "\n".join(lines)
    if intent == "order":
        order = context["order"]
        if not order:
            return "亲，暂时没查到该订单，麻烦您确认订单号是否正确。"
        return f"亲，订单 {order['id']} 当前状态：{order['status']}；物流：{order['logistics']}；售后：{order['after_sales']}"
    if intent == "after_sales":
        return f"亲，售后规则是：{context['policy']} 如果需要处理，我可以继续帮您登记订单号。"
    if intent == "rag":
        chunks = context["chunks"]
        if not chunks:
            return "亲，知识库里暂时没有检索到相关说明，建议您换个说法或提供具体商品名称。"
        lines = [
            f"{item['title']}：{item['content']}（来源：{item['source']}）"
            for item in chunks[:2]
        ]
        return "亲，根据知识库查到：\n" + "\n".join(lines)
    return "亲，我是智能家居客服助手，可以帮您查询商品、订单、物流和售后问题。"


def call_deepseek(query: str, intent: str, context: dict[str, Any]) -> str | None:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        return None

    payload = {
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是电商智能家居客服。请基于给定业务上下文回答，"
                    "语气亲切，回答简洁，不编造上下文之外的订单、库存或知识库内容。"
                    "如果 context 中包含 chunks，请优先依据 chunks，并可简要说明来源。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"question": query, "intent": intent, "context": context},
                    ensure_ascii=False,
                ),
            },
        ],
        "temperature": 0.3,
    }
    try:
        result = deepseek_chat_completion(payload)
        return result["choices"][0]["message"]["content"]
    except (requests.RequestException, RuntimeError, KeyError, TimeoutError, json.JSONDecodeError):
        return None


def run_agent(query: str, conversation_id: str = "demo", user_id: int | None = None) -> dict[str, Any]:
    upsert_conversation(conversation_id, make_conversation_title(query), user_id)
    route = route_query(query)
    context = build_context(route, query)
    answer = call_deepseek(query, route.intent, context) or fallback_response(route.intent, context)
    save_message(conversation_id, "user", query)
    save_message(conversation_id, "assistant", answer)
    upsert_conversation(conversation_id, user_id=user_id)
    return {
        "conversation_id": conversation_id,
        "intent": route.intent,
        "tool_name": route.tool_name,
        "slots": route.slots,
        "route_source": route.source,
        "route_reason": route.reason,
        "route_error": route.error,
        "tool_context": context,
        "answer": answer,
    }
