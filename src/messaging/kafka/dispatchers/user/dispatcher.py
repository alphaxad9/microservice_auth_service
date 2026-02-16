import logging
from typing import Callable, Awaitable, Any

from src.domain.user.events import (
    UserActivated, UserCreated, UserDeactivated,  UserLoggedIn,
    UserEventType,
    UserUpdated,
    UserLoggedOut,
    UserSoftDeleted
)
from src.messaging.user.event_bus import userbus

logger = logging.getLogger(__name__)

# Handler registries: event_type.value -> async handler function
USER_EVENT_HANDLERS: dict[str, Callable[[dict[str, Any]], Awaitable[None]]] = {}


def register_user_handler(event_type: UserEventType):
    def decorator(func: Callable[[dict[str, Any]], Awaitable[None]]):
        USER_EVENT_HANDLERS[event_type.value] = func
        return func
    return decorator


@register_user_handler(UserEventType.USER_CREATED)
async def handle_user_created(data: dict[str, Any]) -> None:
    event = UserCreated.from_dict(data)
    await userbus.publish(event)
    logger.info("✅ UserCreated dispatched")


@register_user_handler(UserEventType.USER_ACTIVATED)
async def handle_user_activated(data: dict[str, Any]) -> None:
    event = UserActivated.from_dict(data)
    await userbus.publish(event)
    logger.info("✅ UserActivated dispatched")


@register_user_handler(UserEventType.USER_DEACTIVATED)
async def handle_user_deactivated(data: dict[str, Any]) -> None:
    event = UserDeactivated.from_dict(data)
    await userbus.publish(event)
    logger.info("✅ UserDeactivated dispatched")



@register_user_handler(UserEventType.USER_LOGGED_IN)
async def handle_user_logged_in(data: dict[str, Any]) -> None:
    event = UserLoggedIn.from_dict(data)
    await userbus.publish(event)
    logger.info("✅ UserLoggedIn dispatched")



@register_user_handler(UserEventType.USER_LOGGED_OUT)
async def handle_user_logged_out(data: dict[str, Any]) -> None:
    event = UserLoggedOut.from_dict(data)
    await userbus.publish(event)
    logger.info("✅ UserLoggedOut dispatched")


@register_user_handler(UserEventType.USER_UPDATED)
async def handle_user_updated(data: dict[str, Any]) -> None:
    event = UserUpdated.from_dict(data)
    await userbus.publish(event)
    logger.info("✅ UserUpdated dispatched")

@register_user_handler(UserEventType.SOFT_DELETED)
async def handle_user_soft_deleted(data: dict[str, Any]) -> None:
    event = UserSoftDeleted.from_dict(data)
    await userbus.publish(event)
    logger.info("✅ SoftDeletion dispatched")