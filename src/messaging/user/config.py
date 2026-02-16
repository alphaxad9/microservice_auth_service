from __future__ import annotations

from src.domain.user.events import (
    UserCreated,
    UserActivated,
    UserDeactivated,
    UserLoggedIn,
    UserLoggedOut,
    UserUpdated,
    UserSoftDeleted
)
from src.application.user.interfaces import UserQueryService
from src.messaging.user.event_bus import UserEventBus
from src.messaging.user.event_handlers import (
    UserEventHandlerContext,
    UserCreatedHandler,
    UserActivatedHandler,
    UserDeactivatedHandler,
    UserLoggedInHandler,
    UserUpdatedHandler,
    UserLoggedOutHandler,
    UserSoftDeletedHandler
)
from src.application.profile.usecases import ProfileUseCase


def configure_user_event_bus(
    event_bus: UserEventBus,
    user_query_service: UserQueryService,
    primary_profile_use_case: ProfileUseCase 

) -> None:
    """
    Register all user-related event handlers with the global user event bus.

    This centralizes handler wiring and ensures domain events from the user
    context trigger appropriate reactions (e.g., logging, analytics, audit trails,
    external notifications, etc.). Currently, handlers log successful event handling.
    """
    # Build shared handler context
    ctx = UserEventHandlerContext(
        user_query_service=user_query_service,
        primary_profile_use_case=primary_profile_use_case
    )
    # Instantiate handlers
    user_created_handler = UserCreatedHandler(ctx=ctx)
    user_activated_handler = UserActivatedHandler(ctx=ctx)
    user_deactivated_handler = UserDeactivatedHandler(ctx=ctx)
    user_logged_in_handler = UserLoggedInHandler(ctx=ctx)
    user_logged_out_handler = UserLoggedOutHandler(ctx=ctx)  # Add handler
    user_updated_handler = UserUpdatedHandler(ctx=ctx)  
    user_soft_deleted_handler = UserSoftDeletedHandler(ctx=ctx) 

    # Subscribe handlers to their respective events
    event_bus.subscribe(UserCreated, user_created_handler.handle)
    event_bus.subscribe(UserActivated, user_activated_handler.handle)
    event_bus.subscribe(UserDeactivated, user_deactivated_handler.handle)
    event_bus.subscribe(UserLoggedIn, user_logged_in_handler.handle)
    event_bus.subscribe(UserLoggedOut, user_logged_out_handler.handle)  
    event_bus.subscribe(UserUpdated, user_updated_handler.handle)  
    event_bus.subscribe(UserSoftDeleted, user_soft_deleted_handler.handle)  