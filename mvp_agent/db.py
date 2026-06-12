from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "customer_agent.sqlite3"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price INTEGER NOT NULL,
                stock INTEGER NOT NULL,
                description TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                logistics TEXT NOT NULL,
                after_sales TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS faqs (
                id INTEGER PRIMARY KEY,
                keyword TEXT NOT NULL,
                answer TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
            );
            """
        )
        product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if product_count == 0:
            conn.executemany(
                "INSERT INTO products(name, category, price, stock, description) VALUES (?, ?, ?, ?, ?)",
                [
                    ("Aster S1 智能门锁", "智能安防", 1299, 18, "支持指纹、密码、临时访客码和低电量提醒。"),
                    ("Luma Pro 智能灯带", "智能照明", 199, 86, "支持手机调光、定时开关和多场景联动。"),
                    ("CleanBot M2 扫地机器人", "智能清洁", 1899, 9, "支持激光建图、自动回充和拖扫一体。"),
                    ("HomeHub Mini 网关", "智能控制", 299, 42, "可连接门锁、灯具、传感器等智能家居设备。"),
                ],
            )
            conn.executemany(
                "INSERT INTO orders(id, status, logistics, after_sales) VALUES (?, ?, ?, ?)",
                [
                    ("SO20260611001", "已发货", "顺丰 SF123456789，预计明天送达", "支持 7 天无理由退货。"),
                    ("SO20260611002", "售后处理中", "无需物流，等待工程师远程诊断", "已创建售后工单，24 小时内反馈。"),
                ],
            )
            conn.executemany(
                "INSERT INTO faqs(keyword, answer) VALUES (?, ?)",
                [
                    ("退货", "支持 7 天无理由退货，商品需保持配件齐全且不影响二次销售。"),
                    ("保修", "智能家居主机类商品默认保修 1 年，电池和耗材按页面说明执行。"),
                    ("发票", "订单完成后可在订单详情页申请电子发票。"),
                    ("安装", "门锁、摄像头等商品可预约上门安装，具体费用以页面展示为准。"),
                ],
            )
        chunk_count = conn.execute("SELECT COUNT(*) FROM knowledge_chunks").fetchone()[0]
        if chunk_count == 0:
            conn.executemany(
                "INSERT INTO knowledge_chunks(title, content, source) VALUES (?, ?, ?)",
                [
                    (
                        "智能门锁安装说明",
                        "Aster S1 智能门锁支持木门、防盗门和部分金属门安装。安装前需要确认门厚在 40 到 100 毫米之间，并保留原锁体照片。下单后可在订单详情中预约上门安装，工程师通常会在 24 小时内联系确认时间。",
                        "install_policy.md",
                    ),
                    (
                        "智能门锁保修政策",
                        "Aster S1 智能门锁主机保修 1 年，指纹识别模块、锁体和主板在非人为损坏情况下可免费维修。电池、螺丝、贴纸等耗材不在整机保修范围内。售后时建议提供订单号、故障视频和门锁序列号。",
                        "warranty_policy.md",
                    ),
                    (
                        "智能灯带使用说明",
                        "Luma Pro 智能灯带支持手机 App 调光、定时开关和场景联动。首次使用需要长按控制器 5 秒进入配网模式，再在 App 中选择 2.4GHz Wi-Fi 进行绑定。灯带不建议安装在高温、潮湿或长期弯折的位置。",
                        "light_strip_manual.md",
                    ),
                    (
                        "扫地机器人维护说明",
                        "CleanBot M2 扫地机器人建议每周清理尘盒和滤网，每月检查边刷、主刷和轮组是否缠绕毛发。若出现无法回充，可先清理充电触点，并确认充电座左右 0.5 米、前方 1.5 米无遮挡。",
                        "robot_maintenance.md",
                    ),
                    (
                        "退货与发票规则",
                        "智能家居商品支持 7 天无理由退货，但商品需保持包装、配件、说明书齐全，且不影响二次销售。订单完成后可申请电子发票，发票抬头和税号需要在申请页面填写。",
                        "after_sales_policy.md",
                    ),
                ],
            )


def make_conversation_title(query: str) -> str:
    title = query.strip().replace("\n", " ")
    return title[:24] or "新会话"


def upsert_conversation(conversation_id: str, title: str | None = None) -> None:
    now = int(time.time())
    with get_conn() as conn:
        row = conn.execute(
            "SELECT conversation_id FROM conversations WHERE conversation_id = ?",
            (conversation_id,),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
                (now, conversation_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO conversations(conversation_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (conversation_id, title or "新会话", now, now),
            )


def save_message(conversation_id: str, role: str, content: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages(conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (conversation_id, role, content, int(time.time())),
        )


def list_conversations(limit: int = 20) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
                c.conversation_id,
                c.title,
                c.created_at,
                c.updated_at,
                (
                    SELECT content
                    FROM messages m
                    WHERE m.conversation_id = c.conversation_id
                    ORDER BY m.id DESC
                    LIMIT 1
                ) AS last_message,
                (
                    SELECT COUNT(*)
                    FROM messages m
                    WHERE m.conversation_id = c.conversation_id
                ) AS message_count
            FROM conversations c
            ORDER BY c.updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_messages(conversation_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,),
        ).fetchall()
        return [dict(row) for row in rows]


