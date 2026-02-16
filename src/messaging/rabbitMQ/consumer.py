import os
import sys
import signal
import time
import logging
import json
import asyncio
from typing import Any, Dict, Optional, Callable, Awaitable

from dotenv import load_dotenv
load_dotenv()

# Django setup
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_backend.settings")
django.setup()

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from django.core.cache import cache

from src.messaging.rabbitMQ.config import (
    RABBIT_USER,
    RABBIT_PORT,
    RABBIT_HOST,
    RABBIT_PASSWORD,
    RABBIT_VHOST,
    RABBIT_QUEUE,
)

logger = logging.getLogger(__name__)
_connection: Optional[pika.BlockingConnection] = None

# ---------------------------------------------------------------------
# Event handlers registry
# ---------------------------------------------------------------------
HANDLER_REGISTRY: dict[str, Callable[[dict[str, Any]], Awaitable[None]]] = {}

# ---------------------------------------------------------------------
# Deduplication (IDEMPOTENCY)
# ---------------------------------------------------------------------
def is_duplicate(message_id: str) -> bool:
    if not message_id or message_id == "unknown":
        return False

    key = f"outbox_processed:{message_id}"
    if cache.get(key):
        return True

    cache.set(key, "1", timeout=7 * 24 * 3600)
    return False


# ---------------------------------------------------------------------
# Domain event dispatcher
# ---------------------------------------------------------------------
async def process_domain_event(event_type: str, event_data: dict[str, Any]) -> None:
    handler = HANDLER_REGISTRY.get(event_type)
    if not handler:
        logger.warning(f"⚠️ No handler registered for {event_type}")
        return

    await handler(event_data)


# ---------------------------------------------------------------------
# RabbitMQ callback
# ---------------------------------------------------------------------
def callback(
    ch: BlockingChannel,
    method: Basic.Deliver,
    properties: BasicProperties,
    body: bytes,
) -> None:
    message_id = properties.message_id or "unknown"

    if is_duplicate(message_id):
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info("🔁 Duplicate message ignored", extra={"message_id": message_id})
        return

    try:
        event_data: Dict[str, Any] = json.loads(body.decode("utf-8"))
        event_type: str = (
            properties.headers.get("event_type", "unknown")
            if properties.headers else "unknown"
        )

        logger.info(
            "📬 EVENT RECEIVED",
            extra={
                "event_type": event_type,
                "message_id": message_id,
            },
        )

        asyncio.run(process_domain_event(event_type, event_data))

        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info("✅ Event processed", extra={"message_id": message_id})

    except Exception as e:
        logger.exception(
            "❌ Event processing failed",
            extra={"error": str(e), "message_id": message_id},
        )

        # Send to DLQ
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        logger.warning("📤 Message sent to DLQ", extra={"message_id": message_id})


# ---------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------
def create_connection() -> pika.BlockingConnection:
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBIT_HOST,
        port=RABBIT_PORT,
        virtual_host=RABBIT_VHOST,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    return pika.BlockingConnection(parameters)


# ---------------------------------------------------------------------
# Consumer startup (DLQ SAFE)
# ---------------------------------------------------------------------
def start_consumer() -> None:
    global _connection

    while True:
        try:
            logger.info("🔌 Connecting to RabbitMQ...")
            _connection = create_connection()
            channel = _connection.channel()

            # Dead-letter infra (safe to redeclare)
            channel.exchange_declare(
                exchange="events.dlx",
                exchange_type="fanout",
                durable=True,
            )

            channel.queue_declare(queue="events.dlq", durable=True)
            channel.queue_bind(queue="events.dlq", exchange="events.dlx")

            # ⚠️ IMPORTANT:
            # Do NOT redefine arguments on an existing queue
            channel.queue_declare(queue=RABBIT_QUEUE, durable=True)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=RABBIT_QUEUE,
                on_message_callback=callback,
            )

            logger.info(f"🚀 Listening on {RABBIT_QUEUE} (DLQ active)")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"RabbitMQ connection error: {e}. Retrying in 5s...")
            time.sleep(5)

        except KeyboardInterrupt:
            logger.info("🛑 Consumer stopped by user")
            break

        except Exception as e:
            logger.exception(f"Unexpected consumer error: {e}")
            break

    if _connection and _connection.is_open:
        _connection.close()


# ---------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------
def signal_handler(sig, frame):
    logger.info("Received shutdown signal")
    if _connection and _connection.is_open:
        _connection.close()
    sys.exit(0)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    start_consumer()
