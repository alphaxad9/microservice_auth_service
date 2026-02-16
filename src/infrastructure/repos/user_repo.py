# src/infrastructure/repos/user_repo.py

from __future__ import annotations
from typing import Sequence
from uuid import UUID
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import IntegrityError, DatabaseError
from django.db.models import Q

from src.domain.user.repository import DomainUserRepository
from src.domain.user.models import DomainUser
from src.domain.user.exceptions import (
    UserNotFoundError,
    UserAlreadyExistsError,
    UserDomainError,
)
from src.infrastructure.apps.users.models import ORMUser
from src.infrastructure.apps.users.mappers import UserMapper


class ORMUserRepository(DomainUserRepository):    
    def __init__(self):
        self.mapper = UserMapper()

    def create(self, user: DomainUser) -> DomainUser:
       
        try:
            # Check if user already exists
            if self._exists_by_email(user.email):
                raise UserAlreadyExistsError(f"User with email '{user.email}' already exists")
            
            if self._exists_by_username(user.username):
                raise UserAlreadyExistsError(f"User with username '{user.username}' already exists")
            
            # Convert to ORM and save
            orm_user = self.mapper.to_orm(user)
            orm_user.save()
            
            # Return domain user with any auto-generated fields
            return self.mapper.to_domain(orm_user)
            
        except IntegrityError as e:
            if 'unique constraint' in str(e).lower():
                if 'email' in str(e).lower():
                    raise UserAlreadyExistsError(f"User with email '{user.email}' already exists") from e
                elif 'username' in str(e).lower():
                    raise UserAlreadyExistsError(f"User with username '{user.username}' already exists") from e
            raise UserDomainError(f"Database integrity error while creating user: {e}") from e
        except DatabaseError as e:
            raise UserDomainError(f"Database error while creating user: {e}") from e
        except Exception as e:
            raise UserDomainError(f"Unexpected error while creating user: {e}") from e

    def by_id(self, user_id: UUID, include_deleted: bool = True) -> DomainUser:
        try:
            query = ORMUser.objects
            if not include_deleted:
                query = query.filter(is_deleted=False)
            
            orm_user = query.get(id=user_id)
            return self.mapper.to_domain(orm_user)
            
        except ObjectDoesNotExist as e:
            raise UserNotFoundError(user_id=str(user_id)) from e
        except DatabaseError as e:
            raise UserDomainError(f"Database error while retrieving user by ID: {e}") from e
        except Exception as e:
            raise UserDomainError(f"Unexpected error while retrieving user by ID: {e}") from e

    def by_email(self, email: str) -> DomainUser:
        """
        Retrieve a user by email (case-insensitive).
        
        Raises:
            UserNotFoundError: If no user exists with the given email.
            UserDomainError: For database errors.
        """
        try:
            orm_user = ORMUser.objects.get(email__iexact=email, is_deleted=False)
            return self.mapper.to_domain(orm_user)
            
        except ObjectDoesNotExist as e:
            raise UserNotFoundError(message=f"User with email '{email}' not found") from e
        except MultipleObjectsReturned as e:
            raise UserDomainError(f"Multiple users found with email '{email}'") from e
        except DatabaseError as e:
            raise UserDomainError(f"Database error while retrieving user by email: {e}") from e
        except Exception as e:
            raise UserDomainError(f"Unexpected error while retrieving user by email: {e}") from e

    def by_username(self, username: str) -> DomainUser:
        """
        Retrieve a user by username (case-insensitive).
        
        Raises:
            UserNotFoundError: If no user exists with the given username.
            UserDomainError: For database errors.
        """
        try:
            orm_user = ORMUser.objects.get(username__iexact=username, is_deleted=False)
            return self.mapper.to_domain(orm_user)
            
        except ObjectDoesNotExist as e:
            raise UserNotFoundError(message=f"User with username '{username}' not found") from e
        except MultipleObjectsReturned as e:
            raise UserDomainError(f"Multiple users found with username '{username}'") from e
        except DatabaseError as e:
            raise UserDomainError(f"Database error while retrieving user by username: {e}") from e
        except Exception as e:
            raise UserDomainError(f"Unexpected error while retrieving user by username: {e}") from e

    def update(self, user: DomainUser) -> DomainUser:
        """
        Update an existing user's mutable fields.
        
        Raises:
            UserNotFoundError: If the user does not exist.
            UserDomainError: For database errors.
        """
        try:
            # Get existing user
            orm_user = ORMUser.objects.get(id=user.user_id, is_deleted=False)
            
            # Check for email/username conflicts with other users
            if ORMUser.objects.filter(email__iexact=user.email).exclude(id=user.user_id).exists():
                raise UserAlreadyExistsError(f"Another user with email '{user.email}' already exists")
            
            if ORMUser.objects.filter(username__iexact=user.username).exclude(id=user.user_id).exists():
                raise UserAlreadyExistsError(f"Another user with username '{user.username}' already exists")
            
            # Update ORM user
            updated_orm_user = self.mapper.to_orm(user, orm_user)
            updated_orm_user.save()
            
            return self.mapper.to_domain(updated_orm_user)
            
        except ObjectDoesNotExist as e:
            raise UserNotFoundError(user_id=str(user.user_id)) from e
        except IntegrityError as e:
            raise UserAlreadyExistsError("User update conflicts with existing data") from e
        except DatabaseError as e:
            raise UserDomainError(f"Database error while updating user: {e}") from e
        except Exception as e:
            raise UserDomainError(f"Unexpected error while updating user: {e}") from e

    def soft_deleted(self, user_id: UUID) -> bool:
        """
        Check if a user is soft-deleted.
        
        Returns:
            bool: True if user exists and is deleted, False if user exists and is not deleted.
        
        Raises:
            UserNotFoundError: If no user exists with the given ID.
            UserDomainError: For database errors.
        """
        try:
            orm_user = ORMUser.objects.get(id=user_id)
            return orm_user.is_deleted
            
        except ObjectDoesNotExist as e:
            raise UserNotFoundError(user_id=str(user_id)) from e
        except DatabaseError as e:
            raise UserDomainError(f"Database error while checking user deletion status: {e}") from e
        except Exception as e:
            raise UserDomainError(f"Unexpected error while checking user deletion status: {e}") from e

    def hard_delete(self, user_id: UUID) -> None:
        """
        Permanently remove a user from the database.
        
        Raises:
            UserNotFoundError: If the user does not exist.
            UserDomainError: For database errors.
        """
        try:
            orm_user = ORMUser.objects.get(id=user_id)
            orm_user.delete()  # This performs a hard delete
            
        except ObjectDoesNotExist as e:
            raise UserNotFoundError(user_id=str(user_id)) from e
        except DatabaseError as e:
            raise UserDomainError(f"Database error while hard deleting user: {e}") from e
        except Exception as e:
            raise UserDomainError(f"Unexpected error while hard deleting user: {e}") from e

    def activate(self, user_id: UUID) -> DomainUser:
        """
        Activate a deactivated user.
        
        Raises:
            UserNotFoundError: If the user does not exist.
            UserDomainError: For database errors.
        """
        try:
            orm_user = ORMUser.objects.get(id=user_id, is_deleted=False)
            orm_user.is_active = True
            orm_user.save()
            
            return self.mapper.to_domain(orm_user)
            
        except ObjectDoesNotExist as e:
            raise UserNotFoundError(user_id=str(user_id)) from e
        except DatabaseError as e:
            raise UserDomainError(f"Database error while activating user: {e}") from e
        except Exception as e:
            raise UserDomainError(f"Unexpected error while activating user: {e}") from e

    def deactivate(self, user_id: UUID) -> DomainUser:
        """
        Deactivate a user.
        
        Raises:
            UserNotFoundError: If the user does not exist.
            UserDomainError: For database errors.
        """
        try:
            orm_user = ORMUser.objects.get(id=user_id, is_deleted=False)
            orm_user.is_active = False
            orm_user.save()
            
            return self.mapper.to_domain(orm_user)
            
        except ObjectDoesNotExist as e:
            raise UserNotFoundError(user_id=str(user_id)) from e
        except DatabaseError as e:
            raise UserDomainError(f"Database error while deactivating user: {e}") from e
        except Exception as e:
            raise UserDomainError(f"Unexpected error while deactivating user: {e}") from e

    def exists_by_email(self, email: str) -> bool:
        """
        Check if a user with the given email exists (case-insensitive).
        """
        try:
            return self._exists_by_email(email)
        except DatabaseError as e:
            raise UserDomainError(f"Database error while checking email existence: {e}") from e
        except Exception as e:
            raise UserDomainError(f"Unexpected error while checking email existence: {e}") from e

    def exists_by_username(self, username: str) -> bool:
        """
        Check if a user with the given username exists (case-insensitive).
        """
        try:
            return self._exists_by_username(username)
        except DatabaseError as e:
            raise UserDomainError(f"Database error while checking username existence: {e}") from e
        except Exception as e:
            raise UserDomainError(f"Unexpected error while checking username existence: {e}") from e

    def list_all(self, limit: int = 100, offset: int = 0, include_deleted: bool = False) -> Sequence[DomainUser]:
        """
        List all users with pagination.
        """
        try:
            query = ORMUser.objects.all()
            if not include_deleted:
                query = query.filter(is_deleted=False)
                
            orm_users = query.order_by('created_at')[offset:offset + limit]
            return [self.mapper.to_domain(user) for user in orm_users]
            
        except DatabaseError as e:
            raise UserDomainError(f"Database error while listing users: {e}") from e
        except Exception as e:
            raise UserDomainError(f"Unexpected error while listing users: {e}") from e

    def search_users(self, query: str, limit: int = 20) -> Sequence[DomainUser]:
        """
        Search users by username, email, first name, or last name.
        """
        try:
            search_filter = (
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )
            
            orm_users = ORMUser.objects.filter(
                search_filter, 
                is_deleted=False
            ).order_by('username')[:limit]
            
            return [self.mapper.to_domain(user) for user in orm_users]
            
        except DatabaseError as e:
            raise UserDomainError(f"Database error while searching users: {e}") from e
        except Exception as e:
            raise UserDomainError(f"Unexpected error while searching users: {e}") from e



    def list_deleted_users(self, limit: int = 100, offset: int = 0) -> Sequence[DomainUser]:
        """
        Retrieve all users who have been soft-deleted.
        """
        try:
            orm_users = ORMUser.objects.filter(
                is_deleted=True
            ).order_by('updated_at')[offset:offset + limit]
            
            return [self.mapper.to_domain(user) for user in orm_users]
            
        except DatabaseError as e:
            raise UserDomainError(f"Database error while listing deleted users: {e}") from e
        except Exception as e:
            raise UserDomainError(f"Unexpected error while listing deleted users: {e}") from e

    # Private helper methods
    def _exists_by_email(self, email: str) -> bool:
        """Internal method to check email existence."""
        return ORMUser.objects.filter(email__iexact=email).exists()

    def _exists_by_username(self, username: str) -> bool:
        """Internal method to check username existence."""
        return ORMUser.objects.filter(username__iexact=username).exists()