# src/application/profile/handlers.py

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.domain.profile.events import (
    ProfileEvent,
    ProfileCreated,
    ProfileUpdated,
    FollowersIncremented,
    FollowersDecremented,
    FollowingIncremented,
    FollowingDecremented,
    NotificationsIncremented,
    UserMarkedOnline,
    NotificationsCleared,
    ProfileSoftDeletedToggled
)
from src.application.profile.interfaces import PrimaryProfileQueryService

logger = logging.getLogger(__name__)


@dataclass
class ProfileEventHandlerContext:
    """
    Dependency container for profile event handlers.
    Can be extended if handlers require additional services.
    """
    profile_query_service: PrimaryProfileQueryService


class BaseProfileEventHandler(ABC):
    """Base class for profile domain event handlers."""

    def __init__(self, ctx: ProfileEventHandlerContext) -> None:
        self.ctx = ctx

    @abstractmethod
    async def handle(self, event: ProfileEvent) -> None:
        raise NotImplementedError


class ProfileCreatedHandler(BaseProfileEventHandler):
    async def handle(self, event: ProfileEvent) -> None:
        if not isinstance(event, ProfileCreated):
            logger.warning("Unexpected event in ProfileCreatedHandler: %s", type(event).__name__)
            return
        logger.info(
            "✅ Handled ProfileCreated: user_id=%s, followers=%s, following=%s, unread_notifications=%s",
            event.user_id,
            event.followers_count,
            event.following_count,
            event.unread_notifications_count,
        )


class ProfileUpdatedHandler(BaseProfileEventHandler):
    async def handle(self, event: ProfileEvent) -> None:
        if not isinstance(event, ProfileUpdated):
            logger.warning("Unexpected event in ProfileUpdatedHandler: %s", type(event).__name__)
            return
        logger.info(
            "✅ Handled ProfileUpdated: user_id=%s, updated_fields=%s",
            event.user_id,
            event.updated_fields,
        )


class FollowersIncrementedHandler(BaseProfileEventHandler):
    async def handle(self, event: ProfileEvent) -> None:
        if not isinstance(event, FollowersIncremented):
            logger.warning("Unexpected event in FollowersIncrementedHandler: %s", type(event).__name__)
            return
        logger.info(
            "✅ Handled FollowersIncremented: user_id=%s, delta=%s, new_count=%s",
            event.user_id,
            event.delta,
            event.new_count,
        )


class FollowersDecrementedHandler(BaseProfileEventHandler):
    async def handle(self, event: ProfileEvent) -> None:
        if not isinstance(event, FollowersDecremented):
            logger.warning("Unexpected event in FollowersDecrementedHandler: %s", type(event).__name__)
            return
        logger.info(
            "✅ Handled FollowersDecremented: user_id=%s, delta=%s, new_count=%s",
            event.user_id,
            event.delta,
            event.new_count,
        )


class FollowingIncrementedHandler(BaseProfileEventHandler):
    async def handle(self, event: ProfileEvent) -> None:
        if not isinstance(event, FollowingIncremented):
            logger.warning("Unexpected event in FollowingIncrementedHandler: %s", type(event).__name__)
            return
        logger.info(
            "✅ Handled FollowingIncremented: user_id=%s, delta=%s, new_count=%s",
            event.user_id,
            event.delta,
            event.new_count,
        )


class FollowingDecrementedHandler(BaseProfileEventHandler):
    async def handle(self, event: ProfileEvent) -> None:
        if not isinstance(event, FollowingDecremented):
            logger.warning("Unexpected event in FollowingDecrementedHandler: %s", type(event).__name__)
            return
        logger.info(
            "✅ Handled FollowingDecremented: user_id=%s, delta=%s, new_count=%s",
            event.user_id,
            event.delta,
            event.new_count,
        )


class NotificationsIncrementedHandler(BaseProfileEventHandler):
    async def handle(self, event: ProfileEvent) -> None:
        if not isinstance(event, NotificationsIncremented):
            logger.warning("Unexpected event in NotificationsIncrementedHandler: %s", type(event).__name__)
            return
        logger.info(
            "✅ Handled NotificationsIncremented: user_id=%s, delta=%s, new_count=%s",
            event.user_id,
            event.delta,
            event.new_count,
        )


class UserMarkedOnlineHandler(BaseProfileEventHandler):
    async def handle(self, event: ProfileEvent) -> None:
        if not isinstance(event, UserMarkedOnline):
            logger.warning("Unexpected event in UserMarkedOnlineHandler: %s", type(event).__name__)
            return
        logger.info(
            "✅ Handled UserMarkedOnline: user_id=%s, last_seen_at=%s",
            event.user_id,
            event.last_seen_at.isoformat(),
        )





class NotificationsClearedHandler(BaseProfileEventHandler):
    async def handle(self, event: ProfileEvent) -> None:
        if not isinstance(event, NotificationsCleared):
            logger.warning("Unexpected event in NotificationsClearedHandler: %s", type(event).__name__)
            return
        logger.info(
            "✅ Handled NotificationsCleared: user_id=%s, previous_count=%s",
            event.user_id,
            event.previous_count,
        )


class ProfileSoftDeletedToggledHandler(BaseProfileEventHandler):
    async def handle(self, event: ProfileEvent) -> None:
        if not isinstance(event, ProfileSoftDeletedToggled):
            logger.warning("Unexpected event in ProfileSoftDeletedToggledHandler: %s", type(event).__name__)
            return
        logger.info(
            "✅ Handled ProfileSoftDeletedToggled: user_id=%s, is_deleted=%s",
            event.user_id,
            event.is_deleted,
        )