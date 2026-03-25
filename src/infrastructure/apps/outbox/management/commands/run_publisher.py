# # src/infrastructure/management/commands/run_publisher.py
# from django.core.management.base import BaseCommand
# from src.messaging.rabbitMQ.publisher import OutboxRabbitPublisher


# class Command(BaseCommand):
#     help = "Run the RabbitMQ publisher to drain the outbox."

#     def handle(self, *args, **options):
#         publisher = OutboxRabbitPublisher()
#         self.stdout.write(self.style.SUCCESS("✅ Starting publisher..."))
#         publisher.start()


# # python manage.py run_publisher
