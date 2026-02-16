# src/application/user/services.py

from __future__ import annotations
from typing import Sequence
from uuid import UUID

from src.domain.user.models import DomainUser
from src.domain.user.repository import DomainUserRepository
from src.domain.user.exceptions import (
    UserNotFoundError,
    UserAlreadyExistsError,
    UserDomainError,
)
from src.application.user.interfaces import UserQueryService, UserCommandService


class UserQueryServiceImpl(UserQueryService):
    """
    Implementation of the UserQueryService interface.
    
    Handles all read operations for user data with proper business logic.
    """

    def __init__(self, user_repository: DomainUserRepository):
        self._user_repository = user_repository

    def get_by_id(self, user_id: UUID, include_deleted: bool = True) -> DomainUser:
        """
        Retrieve a user by their unique ID.
        
        Args:
            user_id: The UUID of the user to retrieve
            include_deleted: Whether to include soft-deleted users (default: True)
            
        Raises:
            UserNotFoundError: If no user exists with the given ID.
        """
        try:
            return self._user_repository.by_id(user_id, include_deleted)
        except UserNotFoundError:
            raise
        except Exception as e:
            raise UserDomainError(f"Error retrieving user by ID: {e}") from e

    def get_by_email(self, email: str) -> DomainUser:
        """
        Retrieve a user by email (case-insensitive).
        
        Raises:
            UserNotFoundError: If no user exists with the given email.
        """
        try:
            return self._user_repository.by_email(email)
        except UserNotFoundError:
            raise
        except Exception as e:
            raise UserDomainError(f"Error retrieving user by email: {e}") from e

    def get_by_username(self, username: str) -> DomainUser:
        """
        Retrieve a user by username (case-insensitive).
        
        Raises:
            UserNotFoundError: If no user exists with the given username.
        """
        try:
            return self._user_repository.by_username(username)
        except UserNotFoundError:
            raise
        except Exception as e:
            raise UserDomainError(f"Error retrieving user by username: {e}") from e

    def user_exists_by_email(self, email: str) -> bool:
        """
        Check if a user with the given email exists (case-insensitive).
        """
        try:
            return self._user_repository.exists_by_email(email)
        except Exception as e:
            raise UserDomainError(f"Error checking email existence: {e}") from e

    def user_exists_by_username(self, username: str) -> bool:
        """
        Check if a user with the given username exists (case-insensitive).
        """
        try:
            return self._user_repository.exists_by_username(username)
        except Exception as e:
            raise UserDomainError(f"Error checking username existence: {e}") from e

    def list_all_users(self, limit: int = 100, offset: int = 0, include_deleted: bool = False) -> Sequence[DomainUser]:
        """
        List all users (typically for admin use). Supports pagination.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            include_deleted: Whether to include soft-deleted users
        """
        try:
            return self._user_repository.list_all(limit, offset, include_deleted)
        except Exception as e:
            raise UserDomainError(f"Error listing users: {e}") from e

    def search_users(self, query: str, limit: int = 20) -> Sequence[DomainUser]:
        """
        Search users by username, email, first name, or last name.
        Used in chat UI for @mentions or adding contacts.
        """
        try:
            if not query or len(query.strip()) == 0:
                return []
            return self._user_repository.search_users(query.strip(), limit)
        except Exception as e:
            raise UserDomainError(f"Error searching users: {e}") from e

    def is_user_soft_deleted(self, user_id: UUID) -> bool:
        """
        Check if a user is soft-deleted.
        
        Returns:
            bool: True if user exists and is deleted, False if user exists and is not deleted.
            
        Raises:
            UserNotFoundError: If no user exists with the given ID.
        """
        try:
            return self._user_repository.soft_deleted(user_id)
        except UserNotFoundError:
            raise
        except Exception as e:
            raise UserDomainError(f"Error checking user deletion status: {e}") from e

    def list_deleted_users(self, limit: int = 100, offset: int = 0) -> Sequence[DomainUser]:
        """
        Retrieve all users who have been soft-deleted (is_deleted=True).
        Supports pagination via limit and offset.
        
        Returns:
            A sequence of soft-deleted User instances.
        """
        try:
            return self._user_repository.list_deleted_users(limit, offset)
        except Exception as e:
            raise UserDomainError(f"Error listing deleted users: {e}") from e


class UserCommandServiceImpl(UserCommandService):
    """
    Implementation of the UserCommandService interface.
    
    Handles all write operations for user data with proper business logic.
    """

    def __init__(self, user_repository: DomainUserRepository, user_query_service: UserQueryService):
        self._user_repository = user_repository
        self._user_query_service = user_query_service

    def update_user(self, user: DomainUser) -> DomainUser:
        """
        Update an existing user's mutable fields (e.g., profile, status).
        
        Raises:
            UserNotFoundError: If the user does not exist.
            UserAlreadyExistsError: If email or username conflicts with another user.
        """
        try:
            # Verify the user exists first
            existing_user = self._user_query_service.get_by_id(user.user_id, include_deleted=False)
            
            # Check for conflicts if email or username changed
            if user.email != existing_user.email:
                if self._user_query_service.user_exists_by_email(user.email):
                    raise UserAlreadyExistsError(f"Another user with email '{user.email}' already exists")
            
            if user.username != existing_user.username:
                if self._user_query_service.user_exists_by_username(user.username):
                    raise UserAlreadyExistsError(f"Another user with username '{user.username}' already exists")
            
            # Update the user
            return self._user_repository.update(user)
            
        except (UserNotFoundError, UserAlreadyExistsError):
            raise
        except Exception as e:
            raise UserDomainError(f"Error updating user: {e}") from e

    def soft_delete_user(self, user_id: UUID) -> DomainUser:
        """
        Mark a user as soft-deleted (set is_deleted=True).
        
        Raises:
            UserNotFoundError: If no user exists with the given ID.
        """
        try:
            # Get the user first to ensure it exists and is not already deleted
            user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            
            # Use the domain method to toggle deleted status
            user.toggle_deleted()
            
            # Update in repository
            return self._user_repository.update(user)
            
        except UserNotFoundError:
            raise
        except Exception as e:
            raise UserDomainError(f"Error soft deleting user: {e}") from e

    def hard_delete_user(self, user_id: UUID) -> None:
        """
        Permanently remove a user from the system.
        
        Raises:
            UserNotFoundError: If the user does not exist.
        """
        try:
            # Verify user exists first
            self._user_query_service.get_by_id(user_id, include_deleted=True)
            
            # Perform hard delete
            self._user_repository.hard_delete(user_id)
            
        except UserNotFoundError:
            raise
        except Exception as e:
            raise UserDomainError(f"Error hard deleting user: {e}") from e

    def activate_user(self, user_id: UUID) -> DomainUser:
        """
        Activate a deactivated user.
        
        Raises:
            UserNotFoundError: If the user does not exist.
        """
        try:
            # Get the user first
            user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            
            # If already active, return as-is
            if user.is_active:
                return user
                
            # Activate the user
            return self._user_repository.activate(user_id)
            
        except UserNotFoundError:
            raise
        except Exception as e:
            raise UserDomainError(f"Error activating user: {e}") from e

    def deactivate_user(self, user_id: UUID) -> DomainUser:
        """
        Deactivate a user (e.g., admin action or self-suspension).
        
        Raises:
            UserNotFoundError: If the user does not exist.
        """
        try:
            # Get the user first
            user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            
            # If already inactive, return as-is
            if not user.is_active:
                return user
                
            # Deactivate the user
            return self._user_repository.deactivate(user_id)
            
        except UserNotFoundError:
            raise
        except Exception as e:
            raise UserDomainError(f"Error deactivating user: {e}") from e

    def update_user_profile(
        self, 
        user_id: UUID, 
        first_name: str | None = None, 
        last_name: str | None = None, 
        profile_picture: str | None = None
    ) -> DomainUser:
        """
        Update user profile information.
        
        Args:
            user_id: The ID of the user to update
            first_name: New first name (optional)
            last_name: New last name (optional)
            profile_picture: New profile picture path (optional)
            
        Raises:
            UserNotFoundError: If the user does not exist.
        """
        try:
            # Get the user first
            user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            
            # Update profile using domain method
            user.update_profile(first_name, last_name, profile_picture)
            
            # Save changes
            return self._user_repository.update(user)
            
        except UserNotFoundError:
            raise
        except Exception as e:
            raise UserDomainError(f"Error updating user profile: {e}") from e

    def toggle_user_active_status(self, user_id: UUID) -> DomainUser:
        """
        Toggle the active status of a user.
        
        Raises:
            UserNotFoundError: If the user does not exist.
        """
        try:
            # Get the user first
            user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            
            # Use domain method to toggle active status
            user.toggle_active()
            
            # Save changes
            return self._user_repository.update(user)
            
        except UserNotFoundError:
            raise
        except Exception as e:
            raise UserDomainError(f"Error toggling user active status: {e}") from e

    def toggle_user_deleted_status(self, user_id: UUID) -> DomainUser:
        """
        Toggle the deleted status of a user.
        
        Raises:
            UserNotFoundError: If the user does not exist.
        """
        try:
            # Get the user first (include deleted users since we're toggling deletion)
            user = self._user_query_service.get_by_id(user_id, include_deleted=True)
            
            # Use domain method to toggle deleted status
            user.toggle_deleted()
            
            # Save changes
            return self._user_repository.update(user)
            
        except UserNotFoundError:
            raise
        except Exception as e:
            raise UserDomainError(f"Error toggling user deleted status: {e}") from e