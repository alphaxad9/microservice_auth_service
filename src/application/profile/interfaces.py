from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID

from src.domain.profile.models import PrimaryProfile


# =========================
# READ INTERFACE (Queries)
# =========================
class PrimaryProfileQueryService(ABC):
    """
    Read-only interface for querying primary profile data.
    """

    @abstractmethod
    def get_by_user_id(self, user_id: UUID) -> PrimaryProfile:
        """
        Retrieve a user's primary profile by user_id.

        Raises:
            ProfileNotFoundError: If no profile exists for the given user_id.
        """
        raise NotImplementedError
    @abstractmethod
    def get_all(self) -> Sequence[PrimaryProfile]:
        """
        Retrieve all non-deleted primary profiles.
        Use with caution—consider pagination or filtering in production.
        """
        raise NotImplementedError
    @abstractmethod
    def exists_for_user(self, user_id: UUID) -> bool:
        """
        Check if a primary profile exists for the given user_id.
        """
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError


# ==========================
# WRITE INTERFACE (Commands)
# ==========================
class PrimaryProfileCommandService(ABC):
    """
    Write interface for mutating primary profile state.
    Encapsulates business logic for profile updates and side effects.
    """

    @abstractmethod
    def create_profile(self, profile: PrimaryProfile) -> PrimaryProfile:
        """
        Create a new primary profile for a user.

        Raises:
            ProfileAlreadyExistsError: If a profile for the user_id already exists.
        """
        raise NotImplementedError

    @abstractmethod
    def update_profile(self, profile: PrimaryProfile) -> PrimaryProfile:
        """
        Update an existing profile (e.g., bio, theme, counts).

        Raises:
            ProfileNotFoundError: If the profile does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def increment_followers(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically increment followers_count.

        Raises:
            ProfileNotFoundError: If profile does not exist.
            ValueError: If delta <= 0.
        """
        raise NotImplementedError

    @abstractmethod
    def decrement_followers(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically decrement followers_count (never below zero).

        Raises:
            ProfileNotFoundError: If profile does not exist.
            ValueError: If delta <= 0.
        """
        raise NotImplementedError

    @abstractmethod
    def increment_following(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically increment following_count.

        Raises:
            ProfileNotFoundError: If profile does not exist.
            ValueError: If delta <= 0.
        """
        raise NotImplementedError

    @abstractmethod
    def decrement_following(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically decrement following_count (never below zero).

        Raises:
            ProfileNotFoundError: If profile does not exist.
            ValueError: If delta <= 0.
        """
        raise NotImplementedError

    @abstractmethod
    def increment_unread_notifications(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically increment unread_notifications_count.

        Raises:
            ProfileNotFoundError: If profile does not exist.
            ValueError: If delta <= 0.
        """
        raise NotImplementedError

    @abstractmethod
    def decrement_unread_notifications(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically decrement unread_notifications_count (never below zero).

        Raises:
            ProfileNotFoundError: If profile does not exist.
            ValueError: If delta <= 0.
        """
        raise NotImplementedError

    @abstractmethod
    def clear_unread_notifications(self, user_id: UUID) -> PrimaryProfile:
        """
        Set unread_notifications_count to zero (only if > 0).

        Raises:
            ProfileNotFoundError: If profile does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def mark_online(self, user_id: UUID) -> PrimaryProfile:
        """
        Update last_seen_at to current UTC time.
        Does NOT update `updated_at`.

        Raises:
            ProfileNotFoundError: If profile does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def toggle_deleted(self, user_id: UUID) -> PrimaryProfile:
        """
        Toggle the `is_deleted` status and update `updated_at`.

        Raises:
            ProfileNotFoundError: If profile does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_permanently(self, user_id: UUID) -> None:
        """
        Permanently remove the profile from storage.

        Raises:
            ProfileNotFoundError: If profile does not exist.
        """
        raise NotImplementedError