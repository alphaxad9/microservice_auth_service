
from __future__ import annotations
from uuid import UUID
import logging
from typing import Sequence, Optional
from src.application.user.dtos import UserDTO
from src.application.user.services import UserQueryServiceImpl, UserCommandServiceImpl
from src.domain.user.events import (
    UserCreated,
    UserActivated,
    UserDeactivated,
    UserLoggedIn,
    UserLoggedOut,
    UserUpdated,
    UserSoftDeleted
)
from typing import Dict, Any
from src.domain.user.exceptions import *
from src.domain.outbox.repositories import OutboxRepository
from src.domain.outbox.events import OutboxEvent
from src.infrastructure.ws.utils.notification_broadcaster import NotificationBroadcaster

logger = logging.getLogger(__name__)


class UserUseCase:
    """
    Command use cases for user operations.
    Handles user management with event publishing and outbox pattern.
    """

    def __init__(
        self,
        user_query_service: UserQueryServiceImpl,
        user_command_service: UserCommandServiceImpl,
        outbox_repo: OutboxRepository,
    ):
        self._user_query_service = user_query_service
        self._user_command_service = user_command_service
        self._outbox_repo = outbox_repo

    # =========================
    # COMMAND USE CASES (Write)
    # =========================

    def publish_user_created_event(self, user_id: UUID) -> UserDTO:
        """
        Publishes a UserCreated event for an already-created user.
        
        Must be called after user creation in infrastructure layer
        to ensure atomicity between user creation and event persistence.
        
        Args:
            user_id: ID of the already-created user
            
        Returns:
            UserDTO: The user as DTO
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            # Get the created user
            user = self._user_query_service.get_by_id(user_id)
            
            # Publish UserCreated event
            domain_event = UserCreated(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
            )
            
            outbox_event = OutboxEvent(
                event_type=domain_event.event_type.value,
                event_payload=domain_event.to_dict(),
                aggregate_id=user.user_id,
                aggregate_type="User",
            )
            self._outbox_repo.save(outbox_event)

            # Notify via WebSocket
            try:
                broadcaster = NotificationBroadcaster()
                broadcaster.send_to_user(
                    user.user_id,
                    {
                        "type": "user_created",
                        "user_id": str(user.user_id),
                        "username": user.username,
                        "email": user.email,
                    },
                )
            except Exception as e:
                logger.warning("Failed to broadcast user creation: %s", e)

            logger.info("User created event published: %s", user.user_id)
            return UserDTO.from_domain(user)

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to publish user created event: %s", e, exc_info=True)
            raise UserDomainError("Failed to publish user creation event.") from e

    def activate_user(self, user_id: UUID) -> UserDTO:
        """
        Activate a user account.
        
        Args:
            user_id: ID of the user to activate
            
        Returns:
            UserDTO: The activated user as DTO
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            # Activate user via command service
            activated_user = self._user_command_service.activate_user(user_id)
            
            # Publish UserActivated event
            domain_event = UserActivated(user_id=user_id)
            outbox_event = OutboxEvent(
                event_type=domain_event.event_type.value,
                event_payload=domain_event.to_dict(),
                aggregate_id=user_id,
                aggregate_type="User",
            )
            self._outbox_repo.save(outbox_event)

            logger.info("User activated: %s", user_id)
            return UserDTO.from_domain(activated_user)

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to activate user: %s", e, exc_info=True)
            raise UserDomainError("Failed to activate user.") from e

    def deactivate_user(self, user_id: UUID) -> UserDTO:
        """
        Deactivate a user account.
        
        Args:
            user_id: ID of the user to deactivate
            
        Returns:
            UserDTO: The deactivated user as DTO
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            # Deactivate user via command service
            deactivated_user = self._user_command_service.deactivate_user(user_id)
            
            # Publish UserDeactivated event
            domain_event = UserDeactivated(user_id=user_id)
            outbox_event = OutboxEvent(
                event_type=domain_event.event_type.value,
                event_payload=domain_event.to_dict(),
                aggregate_id=user_id,
                aggregate_type="User",
            )
            self._outbox_repo.save(outbox_event)

            logger.info("User deactivated: %s", user_id)
            return UserDTO.from_domain(deactivated_user)

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to deactivate user: %s", e, exc_info=True)
            raise UserDomainError("Failed to deactivate user.") from e

    def soft_delete_user(self, user_id: UUID) -> UserDTO:
        """
        Soft delete a user (mark as deleted but keep in database).
        
        Args:
            user_id: ID of the user to delete
            
        Returns:
            UserDTO: The deleted user as DTO
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            # Soft delete user via command service
            deleted_user = self._user_command_service.soft_delete_user(user_id)
            
            # Note: Using UserDeactivated event for soft delete since we don't have UserDeleted
            # You might want to create a UserDeleted event in your domain
            domain_event = UserSoftDeleted(user_id=user_id)
            outbox_event = OutboxEvent(
                event_type=domain_event.event_type.value,
                event_payload=domain_event.to_dict(),
                aggregate_id=user_id,
                aggregate_type="User",
            )
            self._outbox_repo.save(outbox_event)

            logger.info("User soft deleted: %s", user_id)
            return UserDTO.from_domain(deleted_user)

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to soft delete user: %s", e, exc_info=True)
            raise UserDomainError("Failed to delete user.") from e

    def hard_delete_user(self, user_id: UUID) -> None:
        """
        Permanently delete a user from the system.
        
        Args:
            user_id: ID of the user to delete
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            # Hard delete user via command service
            self._user_command_service.hard_delete_user(user_id)
            
            logger.info("User hard deleted: %s", user_id)

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to hard delete user: %s", e, exc_info=True)
            raise UserDomainError("Failed to delete user.") from e

    def update_user_profile(
        self,
        user_id: UUID,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        profile_picture: Optional[str] = None,
    ) -> UserDTO:
        """
        Update user profile information and publish UserUpdated event.
        
        Args:
            user_id: ID of the user to update
            first_name: New first name (optional)
            last_name: New last name (optional)
            profile_picture: New profile picture (optional)
            
        Returns:
            UserDTO: The updated user as DTO
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            # Get current user state for comparison
            current_user = self._user_query_service.get_by_id(user_id)
            
            # Update profile via command service
            updated_user = self._user_command_service.update_user_profile(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                profile_picture=profile_picture,
            )
            
            # Determine which fields were updated
            updated_fields: Dict[str, Any] = {}
            if first_name is not None and first_name != current_user.first_name:
                updated_fields["first_name"] = first_name
            if last_name is not None and last_name != current_user.last_name:
                updated_fields["last_name"] = last_name
            if profile_picture is not None and profile_picture != current_user.profile_picture:
                updated_fields["profile_picture"] = profile_picture
            
            # Publish UserUpdated event if any fields changed
            if updated_fields:
                domain_event = UserUpdated(
                    user_id=user_id,
                    updated_fields=updated_fields,
                )
                outbox_event = OutboxEvent(
                    event_type=domain_event.event_type.value,
                    event_payload=domain_event.to_dict(),
                    aggregate_id=user_id,
                    aggregate_type="User",
                )
                self._outbox_repo.save(outbox_event)

                # Notify via WebSocket
                try:
                    broadcaster = NotificationBroadcaster()
                    broadcaster.send_to_user(
                        user_id,
                        {
                            "type": "user_updated",
                            "user_id": str(user_id),
                            "updated_fields": updated_fields,
                        },
                    )
                except Exception as e:
                    logger.warning("Failed to broadcast user update: %s", e)

            logger.info("User profile updated: %s", user_id)
            return UserDTO.from_domain(updated_user)

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to update user profile: %s", e, exc_info=True)
            raise UserDomainError("Failed to update user profile.") from e

    def toggle_user_active_status(self, user_id: UUID) -> UserDTO:
        """
        Toggle user active status (active/inactive).
        
        Args:
            user_id: ID of the user to toggle
            
        Returns:
            UserDTO: The updated user as DTO
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            # Toggle active status via command service
            updated_user = self._user_command_service.toggle_user_active_status(user_id)
            
            # Determine which event to publish based on new status
            if updated_user.is_active:
                domain_event = UserActivated(user_id=user_id)
            else:
                domain_event = UserDeactivated(user_id=user_id)
                
            outbox_event = OutboxEvent(
                event_type=domain_event.event_type.value,
                event_payload=domain_event.to_dict(),
                aggregate_id=user_id,
                aggregate_type="User",
            )
            self._outbox_repo.save(outbox_event)

            logger.info("User active status toggled: %s (is_active: %s)", user_id, updated_user.is_active)
            return UserDTO.from_domain(updated_user)

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to toggle user active status: %s", e, exc_info=True)
            raise UserDomainError("Failed to toggle user status.") from e

    def log_user_in(
        self,
        user_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Record user login and publish login event.
        
        Args:
            user_id: ID of the user who logged in
            ip_address: IP address of the login (optional)
            user_agent: User agent string (optional)
            
        Raises:
            UserNotFoundError: If user doesn't exist
            UserNotActiveError: If user is not active
        """
        try:
            # Verify user exists and is active
            user = self._user_query_service.get_by_id(user_id)
            if not user.is_active:
                raise UserNotActiveError(str(user_id))

            # Publish UserLoggedIn event
            domain_event = UserLoggedIn(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            outbox_event = OutboxEvent(
                event_type=domain_event.event_type.value,
                event_payload=domain_event.to_dict(),
                aggregate_id=user_id,
                aggregate_type="User",
            )
            self._outbox_repo.save(outbox_event)

            # Notify via WebSocket
            try:
                broadcaster = NotificationBroadcaster()
                broadcaster.send_to_user(
                    user_id,
                    {
                        "type": "user_logged_in",
                        "user_id": str(user_id),
                        "ip_address": ip_address,
                    },
                )
            except Exception as e:
                logger.warning("Failed to broadcast login: %s", e)

            logger.info("User logged in: %s", user_id)

        except (UserNotFoundError, UserNotActiveError):
            raise
        except Exception as e:
            logger.error("Failed to record login: %s", e, exc_info=True)
            raise UserDomainError("Failed to record login.") from e
    def log_user_out(
        self,
        user_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Record user logout and publish logout event.
        
        Args:
            user_id: ID of the user who logged out
            ip_address: IP address of the logout (optional)
            user_agent: User agent string (optional)
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            
            # Publish UserLoggedOut event
            domain_event = UserLoggedOut(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            outbox_event = OutboxEvent(
                event_type=domain_event.event_type.value,
                event_payload=domain_event.to_dict(),
                aggregate_id=user_id,
                aggregate_type="User",
            )
            self._outbox_repo.save(outbox_event)

            # Notify via WebSocket
            try:
                broadcaster = NotificationBroadcaster()
                broadcaster.send_to_user(
                    user_id,
                    {
                        "type": "user_logged_out",
                        "user_id": str(user_id),
                        "ip_address": ip_address,
                    },
                )
            except Exception as e:
                logger.warning("Failed to broadcast logout: %s", e)

            logger.info("User logged out: %s", user_id)

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to record logout: %s", e, exc_info=True)
            raise UserDomainError("Failed to record logout.") from e

    # ========================
    # QUERY USE CASES (Read)
    # ========================

    def get_by_id(self, user_id: UUID, include_deleted: bool = True) -> Optional[UserDTO]:
        """
        Retrieve a user by ID and return as DTO.
        
        Args:
            user_id: ID of the user to retrieve
            include_deleted: Whether to include soft-deleted users
            
        Returns:
            UserDTO: The user as DTO, or None if not found
        """
        try:
            user = self._user_query_service.get_by_id(user_id, include_deleted)
            return UserDTO.from_domain(user) if user else None
        except UserNotFoundError:
            return None
        except Exception as e:
            logger.error("Failed to get user by ID: %s", e, exc_info=True)
            raise UserDomainError("Failed to retrieve user.") from e

    def get_by_email(self, email: str) -> Optional[UserDTO]:
        """
        Retrieve a user by email and return as DTO.
        
        Args:
            email: Email address to search for
            
        Returns:
            UserDTO: The user as DTO, or None if not found
        """
        try:
            user = self._user_query_service.get_by_email(email)
            return UserDTO.from_domain(user) if user else None
        except UserNotFoundError:
            return None
        except Exception as e:
            logger.error("Failed to get user by email: %s", e, exc_info=True)
            raise UserDomainError("Failed to retrieve user.") from e

    def get_by_username(self, username: str) -> Optional[UserDTO]:
        """
        Retrieve a user by username and return as DTO.
        
        Args:
            username: Username to search for
            
        Returns:
            UserDTO: The user as DTO, or None if not found
        """
        try:
            user = self._user_query_service.get_by_username(username)
            return UserDTO.from_domain(user) if user else None
        except UserNotFoundError:
            return None
        except Exception as e:
            logger.error("Failed to get user by username: %s", e, exc_info=True)
            raise UserDomainError("Failed to retrieve user.") from e

    def user_exists_by_email(self, email: str) -> bool:
        """Check if a user exists with the given email."""
        return self._user_query_service.user_exists_by_email(email)

    def user_exists_by_username(self, username: str) -> bool:
        """Check if a user exists with the given username."""
        return self._user_query_service.user_exists_by_username(username)

    def list_all_users(
        self,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False
    ) -> Sequence[UserDTO]:
        """
        List all users with pagination and return as DTOs.
        
        Args:
            limit: Maximum number of users to return (default: 100, max: 1000)
            offset: Number of users to skip (default: 0)
            include_deleted: Whether to include soft-deleted users (default: False)
            
        Returns:
            Sequence[UserDTO]: List of users as DTOs
        """
        try:
            # Validate limit
            if limit > 1000:
                limit = 1000
            if limit < 0:
                limit = 100
            if offset < 0:
                offset = 0

            users = self._user_query_service.list_all_users(
                limit=limit,
                offset=offset,
                include_deleted=include_deleted
            )
            return [UserDTO.from_domain(user) for user in users]
        except Exception as e:
            logger.error("Failed to list users: %s", e, exc_info=True)
            raise UserDomainError("Failed to list users.") from e

    def search_users(self, query: str, limit: int = 20) -> Sequence[UserDTO]:
        """
        Search users by a text query and return as DTOs.
        
        Args:
            query: Search query string
            limit: Maximum number of results (default: 20, max: 100)
            
        Returns:
            Sequence[UserDTO]: List of matching users as DTOs
        """
        try:
            # Validate limit
            if limit > 100:
                limit = 100
            if limit < 0:
                limit = 20

            users = self._user_query_service.search_users(query=query, limit=limit)
            return [UserDTO.from_domain(user) for user in users]
        except Exception as e:
            logger.error("Failed to search users: %s", e, exc_info=True)
            raise UserDomainError("Failed to search users.") from e

    def is_user_active(self, user_id: UUID) -> bool:
        """
        Check if a user is active.
        
        Args:
            user_id: ID of the user to check
            
        Returns:
            bool: True if user exists and is active, False otherwise
        """
        try:
            user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            return user.is_active if user else False
        except UserNotFoundError:
            return False
        except Exception as e:
            logger.error("Failed to check user active status: %s", e, exc_info=True)
            raise UserDomainError("Failed to check user status.") from e

    def is_user_soft_deleted(self, user_id: UUID) -> bool:
        """
        Check if a user is soft-deleted.
        
        Args:
            user_id: ID of the user to check
            
        Returns:
            bool: True if user exists and is deleted, False otherwise
        """
        try:
            return self._user_query_service.is_user_soft_deleted(user_id)
        except UserNotFoundError:
            return False
        except Exception as e:
            logger.error("Failed to check user deletion status: %s", e, exc_info=True)
            raise UserDomainError("Failed to check user deletion status.") from e