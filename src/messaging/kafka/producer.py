import json
import logging
from confluent_kafka import Producer

from .config import (
    KAFKA_BROKERS,
    KAFKA_TOPIC,
)

logger = logging.getLogger(__name__)

producer = Producer({"bootstrap.servers": KAFKA_BROKERS})



def publish_to_kafka(event_type: str, payload: dict, key: str | None = None):
    """
    Publish event to Kafka topic.
    """
    try:
        message = json.dumps({
            "event_type": event_type,
            "payload": payload,
        })

        producer.produce(
            KAFKA_TOPIC,
            key=key.encode("utf-8"),
            value=json.dumps(payload).encode("utf-8"),
            headers=[("event_type", event_type.encode("utf-8"))]
        )

        producer.flush()

        logger.info(f"📨 Sent Kafka event: {event_type}")

    except Exception as e:
        logger.error(f"🔥 Kafka publish failed: {e}")
        raise
