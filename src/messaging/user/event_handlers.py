from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from asgiref.sync import sync_to_async
from src.application.profile.usecases import ProfileUseCase
from src.domain.user.events import (
    UserEvent,
    UserCreated,
    UserActivated,
    UserDeactivated,
    UserLoggedIn,
    UserLoggedOut,
    UserUpdated,
    UserSoftDeleted
)
from src.application.user.interfaces import UserQueryService

logger = logging.getLogger(__name__)


@dataclass
class UserEventHandlerContext:
    """
    Dependency container for user event handlers.
    Currently minimal; can be extended if handlers need services later.
    """
    user_query_service: UserQueryService
    primary_profile_use_case: ProfileUseCase  


class BaseUserEventHandler(ABC):
    """Base class for user domain event handlers."""

    def __init__(self, ctx: UserEventHandlerContext) -> None:
        self.ctx = ctx

    @abstractmethod
    async def handle(self, event: UserEvent) -> None:
        raise NotImplementedError


class UserCreatedHandler(BaseUserEventHandler):
    async def handle(self, event: UserEvent) -> None:
        if not isinstance(event, UserCreated):
            logger.warning("Unexpected event in UserCreatedHandler: %s", type(event).__name__)
            return

        try:
            # Wrap the sync use case call in sync_to_async
            await sync_to_async(self.ctx.primary_profile_use_case.create_profile)(event.user_id)
            logger.info("✅ Profile created for user_id=%s", event.user_id)
        except Exception as e:
            logger.error("❌ Failed to create profile for user_id=%s: %s", event.user_id, e, exc_info=True)
            raise



class UserActivatedHandler(BaseUserEventHandler):
    async def handle(self, event: UserEvent) -> None:
        if not isinstance(event, UserActivated):
            logger.warning("Unexpected event in UserActivatedHandler: %s", type(event).__name__)
            return
        logger.info("✅ Handled UserActivated: user_id=%s", event.user_id)


class UserDeactivatedHandler(BaseUserEventHandler):
    async def handle(self, event: UserEvent) -> None:
        if not isinstance(event, UserDeactivated):
            logger.warning("Unexpected event in UserDeactivatedHandler: %s", type(event).__name__)
            return
        logger.info("✅ Handled UserDeactivated: user_id=%s", event.user_id)


class UserLoggedInHandler(BaseUserEventHandler):
    async def handle(self, event: UserEvent) -> None:
        if not isinstance(event, UserLoggedIn):
            logger.warning("Unexpected event in UserLoggedInHandler: %s", type(event).__name__)
            return
        # Note: payload not stored in event fields, but you could enrich if needed
        logger.info("✅ Handled UserLoggedIn: user_id=%s", event.user_id)


class UserLoggedOutHandler(BaseUserEventHandler):
    async def handle(self, event: UserEvent) -> None:
        if not isinstance(event, UserLoggedOut):
            logger.warning("Unexpected event in UserLoggedOutHandler: %s", type(event).__name__)
            return
        logger.info("✅ Handled UserLoggedOut: user_id=%s, ip_address=%s", 
                    event.user_id, event.ip_address)


class UserUpdatedHandler(BaseUserEventHandler):
    async def handle(self, event: UserEvent) -> None:
        if not isinstance(event, UserUpdated):
            logger.warning("Unexpected event in UserUpdatedHandler: %s", type(event).__name__)
            return
        logger.info("✅ Handled UserUpdated: user_id=%s, updated_fields=%s", 
                    event.user_id, event.updated_fields)
        

class UserSoftDeletedHandler(BaseUserEventHandler):
    async def handle(self, event: UserEvent) -> None:
        if not isinstance(event, UserSoftDeleted):
            logger.warning("Unexpected event in UserUpdatedHandler: %s", type(event).__name__)
            return
        logger.info("✅ Handled soft deleted: user_id=%s", 
                    event.user_id)