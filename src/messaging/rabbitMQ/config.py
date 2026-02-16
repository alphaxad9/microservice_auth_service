import os

RABBIT_HOST: str = os.getenv("RABBITMQ_HOST", "localhost")
RABBIT_PORT: int = int(os.getenv("RABBITMQ_PORT", 5672))
RABBIT_USER: str = os.getenv("RABBITMQ_USER", "guest")
RABBIT_PASSWORD: str = os.getenv("RABBITMQ_PASS", "guest")
RABBIT_VHOST: str = os.getenv("RABBITMQ_VHOST", "my_backend")
RABBIT_QUEUE: str = os.getenv("RABBITMQ_QUEUE", "microservice_one.events")
MAX_RETRIES: int = int(os.getenv("OUTBOX_MAX_RETRIES", 5))
