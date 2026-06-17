from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, Conversation, FAQ, KnowledgeChunk, Message, Order, Product


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE_URL = f"sqlite:///{BASE_DIR / 'customer_agent.sqlite3'}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_runtime_schema()
    with get_session() as session:
        seed_products_orders_faqs(session)
        seed_knowledge_chunks(session)


def ensure_sqlite_runtime_schema() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return
    inspector = inspect(engine)
    if "conversations" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("conversations")}
    if "user_id" in columns:
        return
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE conversations ADD COLUMN user_id INTEGER"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_conversations_user_id ON conversations (user_id)"))


def seed_products_orders_faqs(session: Session) -> None:
    product_count = session.scalar(select(func.count()).select_from(Product))
    if product_count:
        return

    session.add_all(
        [
            Product(
                name="Aster S1 智能门锁",
                category="智能安防",
                price=1299,
                stock=18,
                description="支持指纹、密码、临时访客码和低电量提醒。",
            ),
            Product(
                name="Luma Pro 智能灯带",
                category="智能照明",
                price=199,
                stock=86,
                description="支持手机调光、定时开关和多场景联动。",
            ),
            Product(
                name="CleanBot M2 扫地机器人",
                category="智能清洁",
                price=1899,
                stock=9,
                description="支持激光建图、自动回充和拖扫一体。",
            ),
            Product(
                name="HomeHub Mini 网关",
                category="智能控制",
                price=299,
                stock=42,
                description="可连接门锁、灯具、传感器等智能家居设备。",
            ),
            Order(
                id="SO20260611001",
                status="已发货",
                logistics="顺丰 SF123456789，预计明天送达",
                after_sales="支持 7 天无理由退货。",
            ),
            Order(
                id="SO20260611002",
                status="售后处理中",
                logistics="无需物流，等待工程师远程诊断",
                after_sales="已创建售后工单，24 小时内反馈。",
            ),
            FAQ(keyword="退货", answer="支持 7 天无理由退货，商品需保持配件齐全且不影响二次销售。"),
            FAQ(keyword="保修", answer="智能家居主机类商品默认保修 1 年，电池和耗材按页面说明执行。"),
            FAQ(keyword="发票", answer="订单完成后可在订单详情页申请电子发票。"),
            FAQ(keyword="安装", answer="门锁、摄像头等商品可预约上门安装，具体费用以页面展示为准。"),
        ]
    )


def seed_knowledge_chunks(session: Session) -> None:
    chunk_count = session.scalar(select(func.count()).select_from(KnowledgeChunk))
    if chunk_count:
        return

    session.add_all(
        [
            KnowledgeChunk(
                title="智能门锁安装说明",
                content=(
                    "Aster S1 智能门锁支持木门、防盗门和部分金属门安装。"
                    "安装前需要确认门厚在 40 到 100 毫米之间，并保留原锁体照片。"
                    "下单后可在订单详情中预约上门安装，工程师通常会在 24 小时内联系确认时间。"
                ),
                source="install_policy.md",
            ),
            KnowledgeChunk(
                title="智能门锁保修政策",
                content=(
                    "Aster S1 智能门锁主机保修 1 年，指纹识别模块、锁体和主板在非人为损坏情况下可免费维修。"
                    "电池、螺丝、贴纸等耗材不在整机保修范围内。售后时建议提供订单号、故障视频和门锁序列号。"
                ),
                source="warranty_policy.md",
            ),
            KnowledgeChunk(
                title="智能灯带使用说明",
                content=(
                    "Luma Pro 智能灯带支持手机 App 调光、定时开关和场景联动。"
                    "首次使用需要长按控制器 5 秒进入配网模式，再在 App 中选择 2.4GHz Wi-Fi 进行绑定。"
                    "灯带不建议安装在高温、潮湿或长期弯折的位置。"
                ),
                source="light_strip_manual.md",
            ),
            KnowledgeChunk(
                title="扫地机器人维护说明",
                content=(
                    "CleanBot M2 扫地机器人建议每周清理尘盒和滤网，每月检查边刷、主刷和轮组是否缠绕毛发。"
                    "若出现无法回充，可先清理充电触点，并确认充电座左右 0.5 米、前方 1.5 米无遮挡。"
                ),
                source="robot_maintenance.md",
            ),
            KnowledgeChunk(
                title="退货与发票规则",
                content=(
                    "智能家居商品支持 7 天无理由退货，但商品需保持包装、配件、说明书齐全，且不影响二次销售。"
                    "订单完成后可申请电子发票，发票抬头和税号需要在申请页面填写。"
                ),
                source="after_sales_policy.md",
            ),
        ]
    )


def model_to_dict(model: Any, fields: list[str]) -> dict[str, Any]:
    return {field: getattr(model, field) for field in fields}


def make_conversation_title(query: str) -> str:
    title = query.strip().replace("\n", " ")
    return title[:24] or "新会话"


def upsert_conversation(conversation_id: str, title: str | None = None, user_id: int | None = None) -> None:
    now = int(time.time())
    with get_session() as session:
        conversation = session.get(Conversation, conversation_id)
        if conversation:
            conversation.updated_at = now
            if user_id is not None and conversation.user_id is None:
                conversation.user_id = user_id
        else:
            session.add(
                Conversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    title=title or "新会话",
                    created_at=now,
                    updated_at=now,
                )
            )


def save_message(conversation_id: str, role: str, content: str) -> None:
    with get_session() as session:
        session.add(
            Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                created_at=int(time.time()),
            )
        )


def list_conversations(limit: int = 20, user_id: int | None = None) -> list[dict[str, Any]]:
    with get_session() as session:
        statement = select(Conversation).order_by(Conversation.updated_at.desc()).limit(limit)
        if user_id is None:
            statement = statement.where(Conversation.user_id.is_(None))
        else:
            statement = statement.where(Conversation.user_id == user_id)
        conversations = session.scalars(
            statement
        ).all()
        results: list[dict[str, Any]] = []
        for conversation in conversations:
            last_message = session.scalar(
                select(Message.content)
                .where(Message.conversation_id == conversation.conversation_id)
                .order_by(Message.id.desc())
                .limit(1)
            )
            message_count = session.scalar(
                select(func.count()).select_from(Message).where(Message.conversation_id == conversation.conversation_id)
            )
            results.append(
                {
                    "conversation_id": conversation.conversation_id,
                    "user_id": conversation.user_id,
                    "title": conversation.title,
                    "created_at": conversation.created_at,
                    "updated_at": conversation.updated_at,
                    "last_message": last_message,
                    "message_count": message_count or 0,
                }
            )
        return results


def get_messages(conversation_id: str, user_id: int | None = None) -> list[dict[str, Any]]:
    with get_session() as session:
        conversation = session.get(Conversation, conversation_id)
        if not conversation:
            return []
        if user_id is None and conversation.user_id is not None:
            return []
        if user_id is not None and conversation.user_id != user_id:
            return []
        messages = session.scalars(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id.asc())
        ).all()
        return [
            model_to_dict(message, ["id", "conversation_id", "role", "content", "created_at"])
            for message in messages
        ]
