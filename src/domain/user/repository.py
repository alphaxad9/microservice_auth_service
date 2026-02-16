# src/domain/user/repository.py

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID

from src.domain.user.models import DomainUser


class DomainUserRepository(ABC):
    """
    Contract (interface) for user data persistence in a chat application.
    
    All concrete repositories (e.g., SQLAlchemy, DynamoDB, MongoDB) must implement this.
    """

    @abstractmethod
    def create(self, user: DomainUser) -> DomainUser:
        """
        Persist a new user.
        
        Raises:
            UserAlreadyExistsError: If a user with the same email or username already exists.
        """
        raise NotImplementedError

    @abstractmethod
    def by_id(self, user_id: UUID, include_deleted: bool=True) -> DomainUser:
        """
        Retrieve a user by ID.
        
        Raises:
            UserNotFoundError: If no user exists with the given ID.
        """
        raise NotImplementedError

    @abstractmethod
    def by_email(self, email: str) -> DomainUser:
        """
        Retrieve a user by email (case-insensitive).
        
        Raises:
            UserNotFoundError: If no user exists with the given email.
        """
        raise NotImplementedError

    @abstractmethod
    def by_username(self, username: str) -> DomainUser:
        """
        Retrieve a user by username (case-insensitive).
        
        Raises:
            UserNotFoundError: If no user exists with the given username.
        """
        raise NotImplementedError

    @abstractmethod
    def update(self, user: DomainUser) -> DomainUser:
        """
        Update an existing user's mutable fields (e.g., profile, status).
        
        Raises:
            UserNotFoundError: If the user does not exist.
        """
        raise NotImplementedError
    
    @abstractmethod
    def soft_deleted(self, user_id: UUID) -> bool:
        raise NotImplementedError
    
    
    @abstractmethod
    def hard_delete(self, user_id: UUID) -> None:
        """
        Permanently remove a user (soft-delete not assumed).
        
        Raises:
            UserNotFoundError: If the user does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def activate(self, user_id: UUID) -> DomainUser:
        """
        Activate a deactivated user.
        
        Raises:
            UserNotFoundError: If the user does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def deactivate(self, user_id: UUID) -> DomainUser:
        """
        Deactivate a user (e.g., admin action or self-suspension).
        
        Raises:
            UserNotFoundError: If the user does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """
        Check if a user with the given email exists (case-insensitive).
        Used for validation before creation.
        """
        raise NotImplementedError

    @abstractmethod
    def exists_by_username(self, username: str) -> bool:
        """
        Check if a user with the given username exists (case-insensitive).
        Used for validation before creation.
        """
        raise NotImplementedError

    @abstractmethod
    def list_all(self, limit: int = 100, offset: int = 0, include_deleted: bool=True) -> Sequence[DomainUser]:
        """
        List all users (for admin use). Supports pagination.
        """
        raise NotImplementedError

    @abstractmethod
    def search_users(self, query: str, limit: int = 20) -> Sequence[DomainUser]:
        """
        Search users by username or display name (fuzzy or prefix match).
        Used in chat UI for @mentions or adding contacts.
        """
        raise NotImplementedError

    @abstractmethod
    def list_deleted_users(self, limit: int = 100, offset: int = 0) -> Sequence[DomainUser]:
        """
        Retrieve all users who have been soft-deleted (is_deleted=True).
        Supports pagination via limit and offset.
        
        Returns:
            A sequence of soft-deleted User instances.
        """
        raise NotImplementedError