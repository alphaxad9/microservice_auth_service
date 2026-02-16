# src/messaging/profile/event_bus_config.py

from __future__ import annotations

from src.domain.profile.events import (
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
from src.messaging.profile.event_bus import profilebus  # or import ProfileEventBus and pass instance
from src.messaging.profile.event_handlers import (
    ProfileEventHandlerContext,
    ProfileCreatedHandler,
    ProfileUpdatedHandler,
    FollowersIncrementedHandler,
    FollowersDecrementedHandler,
    FollowingIncrementedHandler,
    FollowingDecrementedHandler,
    NotificationsIncrementedHandler,
    UserMarkedOnlineHandler,
    NotificationsClearedHandler,
    ProfileSoftDeletedToggledHandler
)


def configure_profile_event_bus(
    profile_query_service: PrimaryProfileQueryService,
) -> None:
    """
    Register all profile-related event handlers with the global profile event bus.

    This centralizes handler wiring and ensures domain events from the profile
    context trigger appropriate reactions (e.g., logging, analytics, cache updates,
    or external syncs). Currently, handlers log successful event handling.
    """
    # Build shared handler context
    ctx = ProfileEventHandlerContext(
        profile_query_service=profile_query_service,
    )

    # Instantiate handlers
    profile_created_handler = ProfileCreatedHandler(ctx=ctx)
    profile_updated_handler = ProfileUpdatedHandler(ctx=ctx)
    followers_incremented_handler = FollowersIncrementedHandler(ctx=ctx)
    followers_decremented_handler = FollowersDecrementedHandler(ctx=ctx)
    following_incremented_handler = FollowingIncrementedHandler(ctx=ctx)
    following_decremented_handler = FollowingDecrementedHandler(ctx=ctx)
    notifications_incremented_handler = NotificationsIncrementedHandler(ctx=ctx)
    user_marked_online_handler = UserMarkedOnlineHandler(ctx=ctx)
    notifications_cleared_handler = NotificationsClearedHandler(ctx=ctx)
    profile_soft_deleted_toggled_handler = ProfileSoftDeletedToggledHandler(ctx=ctx)

    # Subscribe handlers to their respective events
    profilebus.subscribe(ProfileCreated, profile_created_handler.handle)
    profilebus.subscribe(ProfileUpdated, profile_updated_handler.handle)
    profilebus.subscribe(FollowersIncremented, followers_incremented_handler.handle)
    profilebus.subscribe(FollowersDecremented, followers_decremented_handler.handle)
    profilebus.subscribe(FollowingIncremented, following_incremented_handler.handle)
    profilebus.subscribe(FollowingDecremented, following_decremented_handler.handle)
    profilebus.subscribe(NotificationsIncremented, notifications_incremented_handler.handle)
    profilebus.subscribe(UserMarkedOnline, user_marked_online_handler.handle)

    profilebus.subscribe(NotificationsCleared, notifications_cleared_handler.handle)
    profilebus.subscribe(ProfileSoftDeletedToggled, profile_soft_deleted_toggled_handler.handle)