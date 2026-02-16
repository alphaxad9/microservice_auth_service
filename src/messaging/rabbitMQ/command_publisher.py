import json
import pika
import logging
from typing import Any, Dict
from src.messaging.rabbitMQ.config import (
    RABBIT_HOST,
    RABBIT_PORT,
    RABBIT_USER,
    RABBIT_PASSWORD,
    RABBIT_VHOST,
)

logger = logging.getLogger(__name__)


class CommandPublisher:
    QUEUE = "auth_service.commands"

    def __init__(self):
        credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASSWORD)
        params = pika.ConnectionParameters(
            host=RABBIT_HOST,
            port=RABBIT_PORT,
            virtual_host=RABBIT_VHOST,
            credentials=credentials,
            heartbeat=60,
        )

        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.QUEUE, durable=True)

    def publish(self, command: str, payload: Dict[str, Any]) -> None:
        self.channel.basic_publish(
            exchange="",
            routing_key=self.QUEUE,
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                headers={"command": command},
            ),
        )
        logger.info(f"📨 Command published: {command}")