# src/domain/profile/repository.py

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID

from src.domain.profile.models import PrimaryProfile


class PrimaryProfileRepository(ABC):
    """
    Contract (interface) for primary profile data persistence.
    
    Manages core social metrics: followers, following, notifications, and online status.
    All concrete implementations (e.g., PostgreSQL, Cassandra) must adhere to this interface.
    """

    @abstractmethod
    def create(self, profile: PrimaryProfile) -> PrimaryProfile:
        """
        Persist a new primary profile for a user.
        
        Raises:
            ProfileAlreadyExistsError: If a profile for the given user_id already exists.
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_user_id(self, user_id: UUID) -> PrimaryProfile:
        """
        Retrieve a user's primary profile by user_id.
        
        Raises:
            ProfileNotFoundError: If no profile exists for the given user_id.
        """
        raise NotImplementedError

    @abstractmethod
    def update(self, profile: PrimaryProfile) -> PrimaryProfile:
        """
        Update an existing profile (e.g., after incrementing counts or marking online).
        Typically updates followers_count, following_count, unread_notifications_count, updated_at.
        Note: last_seen_at updates may bypass `updated_at` per domain logic.
        
        Raises:
            ProfileNotFoundError: If the profile does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def exists_for_user(self, user_id: UUID) -> bool:
        """
        Check if a primary profile exists for the given user_id.
        Used during user creation or profile initialization.
        """
        raise NotImplementedError

    @abstractmethod
    def increment_followers(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically increment the followers_count for a user's profile.
        
        Raises:
            ProfileNotFoundError: If the profile does not exist.
            ValueError: If delta <= 0 (enforced by domain, but repo may validate too).
        """
        raise NotImplementedError

    @abstractmethod
    def decrement_followers(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically decrement the followers_count (never below zero).
        
        Raises:
            ProfileNotFoundError: If the profile does not exist.
            ValueError: If delta <= 0.
        """
        raise NotImplementedError

    @abstractmethod
    def increment_following(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically increment the following_count.
        
        Raises:
            ProfileNotFoundError: If the profile does not exist.
            ValueError: If delta <= 0.
        """
        raise NotImplementedError

    @abstractmethod
    def decrement_following(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically decrement the following_count (never below zero).
        
        Raises:
            ProfileNotFoundError: If the profile does not exist.
            ValueError: If delta <= 0.
        """
        raise NotImplementedError

    @abstractmethod
    def increment_unread_notifications(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically increment the unread_notifications_count.
        
        Raises:
            ProfileNotFoundError: If the profile does not exist.
            ValueError: If delta <= 0.
        """
        raise NotImplementedError


    @abstractmethod
    def mark_online(self, user_id: UUID) -> PrimaryProfile:
        """
        Update the user's last_seen_at to current time.
        Does NOT update `updated_at` (ephemeral signal).
        
        Raises:
            ProfileNotFoundError: If the profile does not exist.
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
        Used for leaderboards or discovery features.
        
        Args:
            by: Field to sort by (e.g., 'followers', 'following'). Must be validated.
            limit: Max number of results.
            offset: Pagination offset.
        """
        raise NotImplementedError

    @abstractmethod
    def decrement_unread_notifications(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        """
        Atomically decrement the unread_notifications_count (never below zero).
        
        Raises:
            ProfileNotFoundError: If the profile does not exist.
            ValueError: If delta <= 0.
        """
        raise NotImplementedError

    @abstractmethod
    def clear_unread_notifications(self, user_id: UUID) -> PrimaryProfile:
        """
        Atomically set unread_notifications_count to zero.
        Only triggers an update if the current count is > 0.
        
        Raises:
            ProfileNotFoundError: If the profile does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def toggle_deleted(self, user_id: UUID) -> PrimaryProfile:
        """
        Toggle the soft-delete status (`is_deleted`) of a user's profile.
        Flips the current state and updates `updated_at`.
        
        Raises:
            ProfileNotFoundError: If the profile does not exist.
        """
        raise NotImplementedError
    

    @abstractmethod
    def delete_permanently(self, user_id: UUID) -> None:
        """
        Permanently delete the user's profile from storage.
        
        Raises:
            ProfileNotFoundError: If the profile does not exist.
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_all(self) -> Sequence[PrimaryProfile]:
        """
        Retrieve all primary profiles (non-deleted by default, unless domain requires otherwise).
        Use with caution in production—consider pagination for large datasets.
        """
        raise NotImplementedError