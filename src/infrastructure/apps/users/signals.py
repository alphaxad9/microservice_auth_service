from django.db.models.signals import post_save, post_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from typing import Type
from uuid import uuid4
import logging
from src.domain.user.events import UserCreatedEvent, UserUpdatedEvent, UserDeletedEvent, UserLogInEvent, UserLogOutEvent
from src.infrastructure.apps.users.models import ORMUser
from src.domain.user.models import DomainUserError
from src.infrastructure.apps.users.mappers import UserMapper
from src.shared.user_bus_config.bus_config import bus
from django.contrib.auth import get_user_model

User = get_user_model()

logger = logging.getLogger(__name__)

@receiver(post_save, sender=ORMUser)
def handle_user_created_or_updated(sender: Type[ORMUser], instance: ORMUser, created: bool, **kwargs) -> None:
    try:
        # Use UserMapper to convert ORMUser to DomainUser for validation
        domain_user = UserMapper.to_domain(instance)
    except DomainUserError as e:
        logger.error(f"Domain validation failed: {e}")
        raise ValueError(f"Domain validation failed: {e}")

    if created:
        event = UserCreatedEvent(
            event_id=uuid4(),
            user_id=domain_user.id,
            username=domain_user.username
        )
    else:
        event = UserUpdatedEvent(
            event_id=uuid4(),
            user_id=domain_user.id,
            username=domain_user.username
        )
    
    try:
        bus.publish(event)
    except Exception as e:
        logger.error(f"Failed to publish event {type(event).__name__}: {e}")
        # Optionally re-raise or handle gracefully depending on requirements
        # raise

@receiver(post_delete, sender=ORMUser)
def handle_user_deleted(sender: Type[ORMUser], instance: ORMUser, **kwargs) -> None:
    try:
        # Validate using UserMapper for consistency
        domain_user = UserMapper.to_domain(instance)
        event = UserDeletedEvent(
            event_id=uuid4(),
            user_id=domain_user.id,
            username=domain_user.username
        )
    except DomainUserError as e:
        logger.error(f"Domain validation failed in delete handler: {e}")
        # Fallback to instance fields if validation fails (optional)
        event = UserDeletedEvent(
            event_id=uuid4(),
            user_id=instance.id,
            username=instance.username
        )
    
    try:
        bus.publish(event)
    except Exception as e:
        logger.error(f"Failed to publish UserDeletedEvent: {e}")

@receiver(user_logged_in, sender=User)
def handle_user_logged_in(sender, user, request, **kwargs):

    try:
        domain_user = UserMapper.to_domain(user)
        event = UserLogInEvent(
            event_id=uuid4(),
            user_id=domain_user.id,
            username=domain_user.username
        )
    except DomainUserError as e:
        event = UserLogInEvent(
            event_id=uuid4(),
            user_id=user.id,
            username=user.username
        )

    try:
        bus.publish(event)
    except Exception as e:
        logger.error(f"❌ Failed to publish UserLogInEvent: {e}")

@receiver(user_logged_out, sender=ORMUser)
def handle_user_logged_out(sender: Type[ORMUser], user: ORMUser, request, **kwargs) -> None:
    try:
        # Validate using UserMapper for consistency
        domain_user = UserMapper.to_domain(user)
        event = UserLogOutEvent(
            event_id=uuid4(),
            user_id=domain_user.id,
            username=domain_user.username
        )
    except DomainUserError as e:
        logger.error(f"Domain validation failed in logout handler: {e}")
        # Fallback to user fields if validation fails (optional)
        event = UserLogOutEvent(
            event_id=uuid4(),
            user_id=user.id,
            username=user.username
        )
    
    try:
        bus.publish(event)
    except Exception as e:
        logger.error(f"Failed to publish UserLogOutEvent: {e}")