from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID
from src.domain.user.models import DomainUser


# =========================
# READ INTERFACE (Queries)
# =========================
class UserQueryService(ABC):
   

    @abstractmethod
    def get_by_id(self, user_id: UUID, include_deleted: bool = True) -> DomainUser:
        
        raise NotImplementedError

    @abstractmethod
    def get_by_email(self, email: str) -> DomainUser:
        
        raise NotImplementedError

    @abstractmethod
    def get_by_username(self, username: str) -> DomainUser:
        """
        Retrieve a user by username (case-insensitive).
        
        Raises:
            UserNotFoundError: If no user exists with the given username.
        """
        raise NotImplementedError

    @abstractmethod
    def user_exists_by_email(self, email: str) -> bool:
        """
        Check if a user with the given email exists (case-insensitive).
        """
        raise NotImplementedError

    @abstractmethod
    def user_exists_by_username(self, username: str) -> bool:
        """
        Check if a user with the given username exists (case-insensitive).
        """
        raise NotImplementedError

    @abstractmethod
    def list_all_users(self, limit: int = 100, offset: int = 0, include_deleted: bool = False) -> Sequence[DomainUser]:
        """
        List all users (typically for admin use). Supports pagination.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            include_deleted: Whether to include soft-deleted users
        """
        raise NotImplementedError

    @abstractmethod
    def search_users(self, query: str, limit: int = 20) -> Sequence[DomainUser]:
        """
        Search users by username, email, first name, or last name.
        Used in chat UI for @mentions or adding contacts.
        """
        raise NotImplementedError

    @abstractmethod
    def is_user_soft_deleted(self, user_id: UUID) -> bool:
        """
        Check if a user is soft-deleted.
        
        Returns:
            bool: True if user exists and is deleted, False if user exists and is not deleted.
            
        Raises:
            UserNotFoundError: If no user exists with the given ID.
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


# ==========================
# WRITE INTERFACE (Commands)
# ==========================
class UserCommandService(ABC):
    """
    High-level interface for user write operations (commands).
    
    Encapsulates business logic for mutating user state.
    """

    @abstractmethod
    def update_user(self, user: DomainUser) -> DomainUser:
        """
        Update an existing user's mutable fields (e.g., profile, status).
        
        Raises:
            UserNotFoundError: If the user does not exist.
            UserAlreadyExistsError: If email or username conflicts with another user.
        """
        raise NotImplementedError

    @abstractmethod
    def soft_delete_user(self, user_id: UUID) -> DomainUser:
        """
        Mark a user as soft-deleted (set is_deleted=True).
        
        Raises:
            UserNotFoundError: If no user exists with the given ID.
        """
        raise NotImplementedError

    @abstractmethod
    def hard_delete_user(self, user_id: UUID) -> None:
        """
        Permanently remove a user from the system.
        
        Raises:
            UserNotFoundError: If the user does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def activate_user(self, user_id: UUID) -> DomainUser:
        """
        Activate a deactivated user.
        
        Raises:
            UserNotFoundError: If the user does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def deactivate_user(self, user_id: UUID) -> DomainUser:
        """
        Deactivate a user (e.g., admin action or self-suspension).
        
        Raises:
            UserNotFoundError: If the user does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def update_user_profile(
        self, 
        user_id: UUID, 
        first_name: str | None = None, 
        last_name: str | None = None, 
        profile_picture: str | None = None
    ) -> DomainUser:
      
        raise NotImplementedError

    @abstractmethod
    def toggle_user_active_status(self, user_id: UUID) -> DomainUser:
        """
        Toggle the active status of a user.
        
        Raises:
            UserNotFoundError: If the user does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def toggle_user_deleted_status(self, user_id: UUID) -> DomainUser:
        """
        Toggle the deleted status of a user.
        
        Raises:
            UserNotFoundError: If the user does not exist.
        """
        raise NotImplementedError