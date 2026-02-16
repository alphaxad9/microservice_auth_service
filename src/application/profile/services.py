from __future__ import annotations
from typing import Sequence
from uuid import UUID

from src.domain.profile.models import PrimaryProfile
from src.domain.profile.repository import PrimaryProfileRepository
from src.domain.profile.exceptions import (
    ProfileNotFoundError,
    ProfileAlreadyExistsError,
    ProfileDomainError,
    InvalidDeltaError
)
from src.application.profile.interfaces import PrimaryProfileQueryService, PrimaryProfileCommandService


class PrimaryProfileQueryServiceImpl(PrimaryProfileQueryService):
    """
    Implementation of the PrimaryProfileQueryService interface.
    
    Handles all read operations for profile data with proper error handling.
    """

    def __init__(self, profile_repository: PrimaryProfileRepository):
        self._profile_repository = profile_repository

    def get_by_user_id(self, user_id: UUID) -> PrimaryProfile:
        """
        Retrieve a user's primary profile by user_id.

        Raises:
            ProfileNotFoundError: If no profile exists for the given user_id.
        """
        try:
            return self._profile_repository.get_by_user_id(user_id)
        except ProfileNotFoundError:
            raise
        except Exception as e:
            raise ProfileDomainError(f"Error retrieving profile by user ID: {e}") from e

    def exists_for_user(self, user_id: UUID) -> bool:
        """
        Check if a primary profile exists for the given user_id.
        """
        try:
            return self._profile_repository.exists_for_user(user_id)
        except Exception as e:
            raise ProfileDomainError(f"Error checking profile existence: {e}") from e

    def list_top_profiles(
        self,
        by: str = "followers",
        limit: int = 20,
        offset: int = 0
    ) -> Sequence[PrimaryProfile]:
        """
        Retrieve top profiles sorted by a metric (e.g., followers_count).

        Args:
            by: Field to sort by (e.g., 'followers', 'following').
            limit: Max number of results.
            offset: Pagination offset.

        Raises:
            ValueError: If `by` is not a supported sort field.
        """
        try:
            if by not in {"followers", "following"}:
                raise ValueError(f"Unsupported sort field: {by}")
            return self._profile_repository.list_top_profiles(by=by, limit=limit, offset=offset)
        except ValueError:
            raise
        except Exception as e:
            raise ProfileDomainError(f"Error listing top profiles: {e}") from e
    def get_all(self) -> Sequence[PrimaryProfile]:
        """
        Retrieve all non-deleted primary profiles.
        """
        try:
            return self._profile_repository.get_all()
        except Exception as e:
            raise ProfileDomainError(f"Error retrieving all profiles: {e}") from e

class PrimaryProfileCommandServiceImpl(PrimaryProfileCommandService):
    """
    Implementation of the PrimaryProfileCommandService interface.
    
    Handles all write operations for profile data with proper business logic.
    """

    def __init__(self, profile_repository: PrimaryProfileRepository, profile_query_service: PrimaryProfileQueryService):
        self._profile_repository = profile_repository
        self._profile_query_service = profile_query_service

    def create_profile(self, profile: PrimaryProfile) -> PrimaryProfile:
        """
        Create a new primary profile for a user.

        Raises:
            ProfileAlreadyExistsError: If a profile for the user_id already exists.
        """
        try:
            # Double-check existence before creation (defense in depth)
            if self._profile_query_service.exists_for_user(profile.user_id):
                raise ProfileAlreadyExistsError(str(profile.user_id))
            
            return self._profile_repository.create(profile)
            
        except ProfileAlreadyExistsError:
            raise
        except Exception as e:
            raise ProfileDomainError(f"Error creating profile: {e}") from e

    def update_profile(self, profile: PrimaryProfile) -> PrimaryProfile:
        """
        Update an existing profile (e.g., bio, theme, counts).

        Raises:
            ProfileNotFoundError: If the profile does not exist.
        """
        try:
            # Verify the profile exists first
            _ = self._profile_query_service.get_by_user_id(profile.user_id)
            return self._profile_repository.update(profile)
            
        except ProfileNotFoundError:
            raise
        except Exception as e:
            raise ProfileDomainError(f"Error updating profile: {e}") from e

    def increment_followers(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically increment followers_count.

        Raises:
            ProfileNotFoundError: If profile does not exist.
            ValueError: If delta <= 0.
        """
        if delta <= 0:
            raise InvalidDeltaError("increment_followers", delta)
        try:
            return self._profile_repository.increment_followers(user_id, delta)
        except ProfileNotFoundError:
            raise
        except Exception as e:
            raise ProfileDomainError(f"Error incrementing followers: {e}") from e

    def decrement_followers(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically decrement followers_count (never below zero).

        Raises:
            ProfileNotFoundError: If profile does not exist.
            ValueError: If delta <= 0.
        """
        if delta <= 0:
            raise InvalidDeltaError("decrement_followers", delta)
        try:
            return self._profile_repository.decrement_followers(user_id, delta)
        except ProfileNotFoundError:
            raise
        except Exception as e:
            raise ProfileDomainError(f"Error decrementing followers: {e}") from e

    def increment_following(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically increment following_count.

        Raises:
            ProfileNotFoundError: If profile does not exist.
            ValueError: If delta <= 0.
        """
        if delta <= 0:
            raise InvalidDeltaError("increment_following", delta)
        try:
            return self._profile_repository.increment_following(user_id, delta)
        except ProfileNotFoundError:
            raise
        except Exception as e:
            raise ProfileDomainError(f"Error incrementing following: {e}") from e

    def decrement_following(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically decrement following_count (never below zero).

        Raises:
            ProfileNotFoundError: If profile does not exist.
            ValueError: If delta <= 0.
        """
        if delta <= 0:
            raise InvalidDeltaError("decrement_following", delta)
        try:
            return self._profile_repository.decrement_following(user_id, delta)
        except ProfileNotFoundError:
            raise
        except Exception as e:
            raise ProfileDomainError(f"Error decrementing following: {e}") from e

    def increment_unread_notifications(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically increment unread_notifications_count.

        Raises:
            ProfileNotFoundError: If profile does not exist.
            ValueError: If delta <= 0.
        """
        if delta <= 0:
            raise InvalidDeltaError("increment_unread_notifications", delta)
        try:
            return self._profile_repository.increment_unread_notifications(user_id, delta)
        except ProfileNotFoundError:
            raise
        except Exception as e:
            raise ProfileDomainError(f"Error incrementing notifications: {e}") from e

    def decrement_unread_notifications(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically decrement unread_notifications_count (never below zero).

        Raises:
            ProfileNotFoundError: If profile does not exist.
            ValueError: If delta <= 0.
        """
        if delta <= 0:
            raise InvalidDeltaError("decrement_unread_notifications", delta)
        try:
            return self._profile_repository.decrement_unread_notifications(user_id, delta)
        except ProfileNotFoundError:
            raise
        except Exception as e:
            raise ProfileDomainError(f"Error decrementing notifications: {e}") from e

    def clear_unread_notifications(self, user_id: UUID) -> PrimaryProfile:
        """
        Set unread_notifications_count to zero (only if > 0).

        Raises:
            ProfileNotFoundError: If profile does not exist.
        """
        try:
            return self._profile_repository.clear_unread_notifications(user_id)
        except ProfileNotFoundError:
            raise
        except Exception as e:
            raise ProfileDomainError(f"Error clearing notifications: {e}") from e

    def mark_online(self, user_id: UUID) -> PrimaryProfile:
        """
        Update last_seen_at to current UTC time.
        Does NOT update `updated_at`.

        Raises:
            ProfileNotFoundError: If profile does not exist.
        """
        try:
            return self._profile_repository.mark_online(user_id)
        except ProfileNotFoundError:
            raise
        except Exception as e:
            raise ProfileDomainError(f"Error marking user online: {e}") from e

    def toggle_deleted(self, user_id: UUID) -> PrimaryProfile:
        """
        Toggle the `is_deleted` status and update `updated_at`.

        Raises:
            ProfileNotFoundError: If profile does not exist.
        """
        try:
            # Load current profile
            profile = self._profile_query_service.get_by_user_id(user_id)
            # Toggle in domain model
            profile.toggle_deleted()
            # Persist
            return self._profile_repository.update(profile)
        except ProfileNotFoundError:
            raise
        except Exception as e:
            raise ProfileDomainError(f"Error toggling profile deletion: {e}") from e

    def delete_permanently(self, user_id: UUID) -> None:
        """
        Permanently remove the profile from storage.

        Raises:
            ProfileNotFoundError: If profile does not exist.
        """
        try:
            # Verify existence first
            _ = self._profile_query_service.get_by_user_id(user_id)
            self._profile_repository.delete_permanently(user_id)
        except ProfileNotFoundError:
            raise
        except Exception as e:
            raise ProfileDomainError(f"Error permanently deleting profile: {e}") from e