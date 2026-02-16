# src/messaging/profile/dispatcher.py

import logging
from typing import Callable, Awaitable, Any

from src.domain.profile.events import (
    ProfileCreated,
    ProfileUpdated,
    FollowersIncremented,
    FollowersDecremented,
    FollowingIncremented,
    FollowingDecremented,
    NotificationsIncremented,
    UserMarkedOnline,
    ProfileEventType,
    ProfileSoftDeletedToggled,
    NotificationsCleared
)
from src.messaging.profile.event_bus import profilebus

logger = logging.getLogger(__name__)

# Handler registry: event_type.value -> async handler function
PROFILE_EVENT_HANDLERS: dict[str, Callable[[dict[str, Any]], Awaitable[None]]] = {}


def register_profile_handler(event_type: ProfileEventType):
    def decorator(func: Callable[[dict[str, Any]], Awaitable[None]]):
        PROFILE_EVENT_HANDLERS[event_type.value] = func
        return func
    return decorator


@register_profile_handler(ProfileEventType.PROFILE_CREATED)
async def handle_profile_created(data: dict[str, Any]) -> None:
    event = ProfileCreated.from_dict(data)
    await profilebus.publish(event)
    logger.info("✅ ProfileCreated dispatched")


@register_profile_handler(ProfileEventType.PROFILE_UPDATED)
async def handle_profile_updated(data: dict[str, Any]) -> None:
    event = ProfileUpdated.from_dict(data)
    await profilebus.publish(event)
    logger.info("✅ ProfileUpdated dispatched")


@register_profile_handler(ProfileEventType.FOLLOWERS_INCREMENTED)
async def handle_followers_incremented(data: dict[str, Any]) -> None:
    event = FollowersIncremented.from_dict(data)
    await profilebus.publish(event)
    logger.info("✅ FollowersIncremented dispatched")


@register_profile_handler(ProfileEventType.FOLLOWERS_DECREMENTED)
async def handle_followers_decremented(data: dict[str, Any]) -> None:
    event = FollowersDecremented.from_dict(data)
    await profilebus.publish(event)
    logger.info("✅ FollowersDecremented dispatched")


@register_profile_handler(ProfileEventType.FOLLOWING_INCREMENTED)
async def handle_following_incremented(data: dict[str, Any]) -> None:
    event = FollowingIncremented.from_dict(data)
    await profilebus.publish(event)
    logger.info("✅ FollowingIncremented dispatched")


@register_profile_handler(ProfileEventType.FOLLOWING_DECREMENTED)
async def handle_following_decremented(data: dict[str, Any]) -> None:
    event = FollowingDecremented.from_dict(data)
    await profilebus.publish(event)
    logger.info("✅ FollowingDecremented dispatched")


@register_profile_handler(ProfileEventType.NOTIFICATIONS_INCREMENTED)
async def handle_notifications_incremented(data: dict[str, Any]) -> None:
    event = NotificationsIncremented.from_dict(data)
    await profilebus.publish(event)
    logger.info("✅ NotificationsIncremented dispatched")


@register_profile_handler(ProfileEventType.USER_MARKED_ONLINE)
async def handle_user_marked_online(data: dict[str, Any]) -> None:
    event = UserMarkedOnline.from_dict(data)
    await profilebus.publish(event)
    logger.info("✅ UserMarkedOnline dispatched")

@register_profile_handler(ProfileEventType.NOTIFICATIONS_CLEARED)  # <-- ADD THIS
async def handle_notifications_cleared(data: dict[str, Any]) -> None:
    event = NotificationsCleared.from_dict(data)
    await profilebus.publish(event)
    logger.info("✅ NotificationsCleared dispatched")


@register_profile_handler(ProfileEventType.PROFILE_SOFT_DELETED_TOGGLED)  # Already imported, but ensure handler exists
async def handle_profile_soft_deleted_toggled(data: dict[str, Any]) -> None:
    event = ProfileSoftDeletedToggled.from_dict(data)
    await profilebus.publish(event)
    logger.info("✅ ProfileSoftDeletedToggled dispatched")