# tests/application/user/test_services.py

import pytest
from uuid import uuid4, UUID
from unittest.mock import Mock, patch
from typing import Sequence

from src.application.user.services import UserQueryServiceImpl, UserCommandServiceImpl
from src.domain.user.models import DomainUser
from src.domain.user.repository import DomainUserRepository
from src.domain.user.exceptions import (
    UserNotFoundError,
    UserAlreadyExistsError,
    UserDomainError,
)


@pytest.fixture
def mock_user_repository():
    return Mock(spec=DomainUserRepository)


@pytest.fixture
def mock_query_service():
    return Mock(spec=UserQueryServiceImpl)


@pytest.fixture
def sample_domain_user():
    return DomainUser(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        is_active=True,
        is_deleted=False
    )


@pytest.fixture
def sample_user_id():
    return uuid4()


class TestUserQueryServiceImpl:
    
    def test_get_by_id_success(self, mock_user_repository, sample_domain_user, sample_user_id):
        # Arrange
        mock_user_repository.by_id.return_value = sample_domain_user
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act
        result = query_service.get_by_id(sample_user_id)
        
        # Assert
        assert result == sample_domain_user
        # Fix: Use positional arguments instead of keyword arguments
        mock_user_repository.by_id.assert_called_once_with(sample_user_id, True)
    def test_get_by_id_with_include_deleted_false(self, mock_user_repository, sample_domain_user, sample_user_id):
        # Arrange
        mock_user_repository.by_id.return_value = sample_domain_user
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act
        result = query_service.get_by_id(sample_user_id, include_deleted=False)
        
        # Assert
        assert result == sample_domain_user
        # Fix: Use positional arguments instead of keyword arguments
        mock_user_repository.by_id.assert_called_once_with(sample_user_id, False)


    def test_get_by_id_not_found(self, mock_user_repository, sample_user_id):
        # Arrange
        mock_user_repository.by_id.side_effect = UserNotFoundError(user_id=str(sample_user_id))
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            query_service.get_by_id(sample_user_id)

    def test_get_by_id_unexpected_error(self, mock_user_repository, sample_user_id):
        # Arrange
        mock_user_repository.by_id.side_effect = Exception("Database connection failed")
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act & Assert
        with pytest.raises(UserDomainError) as exc_info:
            query_service.get_by_id(sample_user_id)
        assert "Error retrieving user by ID" in str(exc_info.value)

    def test_get_by_email_success(self, mock_user_repository, sample_domain_user):
        # Arrange
        mock_user_repository.by_email.return_value = sample_domain_user
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act
        result = query_service.get_by_email("test@example.com")
        
        # Assert
        assert result == sample_domain_user
        mock_user_repository.by_email.assert_called_once_with("test@example.com")

    def test_get_by_email_not_found(self, mock_user_repository):
        # Arrange
        mock_user_repository.by_email.side_effect = UserNotFoundError(message="User not found")
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            query_service.get_by_email("nonexistent@example.com")

    def test_get_by_username_success(self, mock_user_repository, sample_domain_user):
        # Arrange
        mock_user_repository.by_username.return_value = sample_domain_user
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act
        result = query_service.get_by_username("testuser")
        
        # Assert
        assert result == sample_domain_user
        mock_user_repository.by_username.assert_called_once_with("testuser")

    def test_user_exists_by_email_true(self, mock_user_repository):
        # Arrange
        mock_user_repository.exists_by_email.return_value = True
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act
        result = query_service.user_exists_by_email("test@example.com")
        
        # Assert
        assert result is True
        mock_user_repository.exists_by_email.assert_called_once_with("test@example.com")

    def test_user_exists_by_email_false(self, mock_user_repository):
        # Arrange
        mock_user_repository.exists_by_email.return_value = False
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act
        result = query_service.user_exists_by_email("test@example.com")
        
        # Assert
        assert result is False

    def test_user_exists_by_username_true(self, mock_user_repository):
        # Arrange
        mock_user_repository.exists_by_username.return_value = True
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act
        result = query_service.user_exists_by_username("testuser")
        
        # Assert
        assert result is True
        mock_user_repository.exists_by_username.assert_called_once_with("testuser")

    def test_list_all_users_success(self, mock_user_repository, sample_domain_user):
        # Arrange
        mock_user_repository.list_all.return_value = [sample_domain_user]
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act
        result = query_service.list_all_users(limit=10, offset=0, include_deleted=False)
        
        # Assert
        assert result == [sample_domain_user]
        mock_user_repository.list_all.assert_called_once_with(10, 0, False)

    def test_list_all_users_default_params(self, mock_user_repository, sample_domain_user):
        # Arrange
        mock_user_repository.list_all.return_value = [sample_domain_user]
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act
        result = query_service.list_all_users()
        
        # Assert
        assert result == [sample_domain_user]
        mock_user_repository.list_all.assert_called_once_with(100, 0, False)

    def test_search_users_success(self, mock_user_repository, sample_domain_user):
        # Arrange
        mock_user_repository.search_users.return_value = [sample_domain_user]
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act
        result = query_service.search_users("test", limit=10)
        
        # Assert
        assert result == [sample_domain_user]
        mock_user_repository.search_users.assert_called_once_with("test", 10)

    def test_search_users_empty_query(self, mock_user_repository):
        # Arrange
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act
        result = query_service.search_users("")
        
        # Assert
        assert result == []
        mock_user_repository.search_users.assert_not_called()

    def test_search_users_whitespace_query(self, mock_user_repository):
        # Arrange
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act
        result = query_service.search_users("   ")
        
        # Assert
        assert result == []
        mock_user_repository.search_users.assert_not_called()

    def test_is_user_soft_deleted_true(self, mock_user_repository, sample_user_id):
        # Arrange
        mock_user_repository.soft_deleted.return_value = True
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act
        result = query_service.is_user_soft_deleted(sample_user_id)
        
        # Assert
        assert result is True
        mock_user_repository.soft_deleted.assert_called_once_with(sample_user_id)

    def test_is_user_soft_deleted_false(self, mock_user_repository, sample_user_id):
        # Arrange
        mock_user_repository.soft_deleted.return_value = False
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act
        result = query_service.is_user_soft_deleted(sample_user_id)
        
        # Assert
        assert result is False

    def test_list_deleted_users_success(self, mock_user_repository, sample_domain_user):
        # Arrange
        deleted_user = DomainUser(
            username="deleteduser",
            email="deleted@example.com",
            is_deleted=True
        )
        mock_user_repository.list_deleted_users.return_value = [deleted_user]
        query_service = UserQueryServiceImpl(mock_user_repository)
        
        # Act
        result = query_service.list_deleted_users(limit=50, offset=10)
        
        # Assert
        assert result == [deleted_user]
        mock_user_repository.list_deleted_users.assert_called_once_with(50, 10)


class TestUserCommandServiceImpl:
    
    def test_update_user_success(self, mock_user_repository, mock_query_service, sample_domain_user, sample_user_id):
        # Arrange
        mock_query_service.get_by_id.return_value = sample_domain_user
        mock_query_service.user_exists_by_email.return_value = False
        mock_query_service.user_exists_by_username.return_value = False
        mock_user_repository.update.return_value = sample_domain_user
        
        command_service = UserCommandServiceImpl(mock_user_repository, mock_query_service)
        
        # Act
        result = command_service.update_user(sample_domain_user)
        
        # Assert
        assert result == sample_domain_user
        mock_query_service.get_by_id.assert_called_once_with(sample_domain_user.user_id, include_deleted=False)
        mock_user_repository.update.assert_called_once_with(sample_domain_user)

    def test_update_user_email_conflict(self, mock_user_repository, mock_query_service, sample_domain_user):
        # Arrange
        # Create a different user to simulate email conflict
        existing_user = DomainUser(
            username="existinguser",
            email="existing@example.com",
            user_id=sample_domain_user.user_id
        )
        mock_query_service.get_by_id.return_value = existing_user
        mock_query_service.user_exists_by_email.return_value = True
        
        command_service = UserCommandServiceImpl(mock_user_repository, mock_query_service)
        
        # Act & Assert
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            command_service.update_user(sample_domain_user)
        
        assert "email" in str(exc_info.value).lower()
        mock_user_repository.update.assert_not_called()


    def test_update_user_username_conflict(self, mock_user_repository, mock_query_service, sample_domain_user):
        # Arrange
        # Create a different user to simulate username conflict
        existing_user = DomainUser(
            username="existinguser", 
            email="existing@example.com",
            user_id=sample_domain_user.user_id
        )
        mock_query_service.get_by_id.return_value = existing_user
        mock_query_service.user_exists_by_email.return_value = False
        mock_query_service.user_exists_by_username.return_value = True
        
        command_service = UserCommandServiceImpl(mock_user_repository, mock_query_service)
        
        # Act & Assert
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            command_service.update_user(sample_domain_user)
        
        assert "username" in str(exc_info.value).lower()
        mock_user_repository.update.assert_not_called()

    def test_update_user_not_found(self, mock_user_repository, mock_query_service, sample_domain_user):
        # Arrange
        mock_query_service.get_by_id.side_effect = UserNotFoundError(user_id=str(sample_domain_user.user_id))
        
        command_service = UserCommandServiceImpl(mock_user_repository, mock_query_service)
        
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            command_service.update_user(sample_domain_user)
        
        mock_user_repository.update.assert_not_called()

    def test_soft_delete_user_success(self, mock_user_repository, mock_query_service, sample_domain_user, sample_user_id):
        # Arrange
        sample_domain_user.user_id = sample_user_id
        mock_query_service.get_by_id.return_value = sample_domain_user
        mock_user_repository.update.return_value = sample_domain_user
        
        command_service = UserCommandServiceImpl(mock_user_repository, mock_query_service)
        
        # Act
        result = command_service.soft_delete_user(sample_user_id)
        
        # Assert
        assert result == sample_domain_user
        mock_query_service.get_by_id.assert_called_once_with(sample_user_id, include_deleted=False)
        mock_user_repository.update.assert_called_once_with(sample_domain_user)
        # Verify toggle_deleted was called
        assert sample_domain_user.is_deleted is True

    def test_hard_delete_user_success(self, mock_user_repository, mock_query_service, sample_user_id):
        # Arrange
        mock_query_service.get_by_id.return_value = Mock()
        
        command_service = UserCommandServiceImpl(mock_user_repository, mock_query_service)
        
        # Act
        command_service.hard_delete_user(sample_user_id)
        
        # Assert
        mock_query_service.get_by_id.assert_called_once_with(sample_user_id, include_deleted=True)
        mock_user_repository.hard_delete.assert_called_once_with(sample_user_id)

    def test_hard_delete_user_not_found(self, mock_user_repository, mock_query_service, sample_user_id):
        # Arrange
        mock_query_service.get_by_id.side_effect = UserNotFoundError(user_id=str(sample_user_id))
        
        command_service = UserCommandServiceImpl(mock_user_repository, mock_query_service)
        
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            command_service.hard_delete_user(sample_user_id)
        
        mock_user_repository.hard_delete.assert_not_called()

    def test_activate_user_success(self, mock_user_repository, mock_query_service, sample_domain_user, sample_user_id):
        # Arrange
        sample_domain_user.is_active = False
        sample_domain_user.user_id = sample_user_id
        mock_query_service.get_by_id.return_value = sample_domain_user
        mock_user_repository.activate.return_value = sample_domain_user
        
        command_service = UserCommandServiceImpl(mock_user_repository, mock_query_service)
        
        # Act
        result = command_service.activate_user(sample_user_id)
        
        # Assert
        assert result == sample_domain_user
        mock_query_service.get_by_id.assert_called_once_with(sample_user_id, include_deleted=False)
        mock_user_repository.activate.assert_called_once_with(sample_user_id)

    def test_activate_user_already_active(self, mock_user_repository, mock_query_service, sample_domain_user, sample_user_id):
        # Arrange
        sample_domain_user.is_active = True
        sample_domain_user.user_id = sample_user_id
        mock_query_service.get_by_id.return_value = sample_domain_user
        
        command_service = UserCommandServiceImpl(mock_user_repository, mock_query_service)
        
        # Act
        result = command_service.activate_user(sample_user_id)
        
        # Assert
        assert result == sample_domain_user
        mock_query_service.get_by_id.assert_called_once_with(sample_user_id, include_deleted=False)
        mock_user_repository.activate.assert_not_called()

    def test_deactivate_user_success(self, mock_user_repository, mock_query_service, sample_domain_user, sample_user_id):
        # Arrange
        sample_domain_user.is_active = True
        sample_domain_user.user_id = sample_user_id
        mock_query_service.get_by_id.return_value = sample_domain_user
        mock_user_repository.deactivate.return_value = sample_domain_user
        
        command_service = UserCommandServiceImpl(mock_user_repository, mock_query_service)
        
        # Act
        result = command_service.deactivate_user(sample_user_id)
        
        # Assert
        assert result == sample_domain_user
        mock_query_service.get_by_id.assert_called_once_with(sample_user_id, include_deleted=False)
        mock_user_repository.deactivate.assert_called_once_with(sample_user_id)

    def test_update_user_profile_success(self, mock_user_repository, mock_query_service, sample_domain_user, sample_user_id):
        # Arrange
        sample_domain_user.user_id = sample_user_id
        mock_query_service.get_by_id.return_value = sample_domain_user
        mock_user_repository.update.return_value = sample_domain_user
        
        command_service = UserCommandServiceImpl(mock_user_repository, mock_query_service)
        
        # Act
        result = command_service.update_user_profile(
            sample_user_id,
            first_name="NewFirst",
            last_name="NewLast",
            profile_picture="new_picture.jpg"
        )
        
        # Assert
        assert result == sample_domain_user
        mock_query_service.get_by_id.assert_called_once_with(sample_user_id, include_deleted=False)
        mock_user_repository.update.assert_called_once_with(sample_domain_user)
        # Verify profile was updated
        assert sample_domain_user.first_name == "NewFirst"
        assert sample_domain_user.last_name == "NewLast"
        assert sample_domain_user.profile_picture == "new_picture.jpg"

    def test_toggle_user_active_status_success(self, mock_user_repository, mock_query_service, sample_domain_user, sample_user_id):
        # Arrange
        sample_domain_user.user_id = sample_user_id
        sample_domain_user.is_active = True
        mock_query_service.get_by_id.return_value = sample_domain_user
        mock_user_repository.update.return_value = sample_domain_user
        
        command_service = UserCommandServiceImpl(mock_user_repository, mock_query_service)
        
        # Act
        result = command_service.toggle_user_active_status(sample_user_id)
        
        # Assert
        assert result == sample_domain_user
        mock_query_service.get_by_id.assert_called_once_with(sample_user_id, include_deleted=False)
        mock_user_repository.update.assert_called_once_with(sample_domain_user)
        # Verify active status was toggled
        assert sample_domain_user.is_active is False

    def test_toggle_user_deleted_status_success(self, mock_user_repository, mock_query_service, sample_domain_user, sample_user_id):
        # Arrange
        sample_domain_user.user_id = sample_user_id
        sample_domain_user.is_deleted = False
        mock_query_service.get_by_id.return_value = sample_domain_user
        mock_user_repository.update.return_value = sample_domain_user
        
        command_service = UserCommandServiceImpl(mock_user_repository, mock_query_service)
        
        # Act
        result = command_service.toggle_user_deleted_status(sample_user_id)
        
        # Assert
        assert result == sample_domain_user
        mock_query_service.get_by_id.assert_called_once_with(sample_user_id, include_deleted=True)
        mock_user_repository.update.assert_called_once_with(sample_domain_user)
        # Verify deleted status was toggled
        assert sample_domain_user.is_deleted is True

    def test_command_service_unexpected_error(self, mock_user_repository, mock_query_service, sample_user_id):
        # Arrange
        mock_query_service.get_by_id.side_effect = Exception("Unexpected error")
        command_service = UserCommandServiceImpl(mock_user_repository, mock_query_service)
        
        # Act & Assert
        with pytest.raises(UserDomainError) as exc_info:
            command_service.activate_user(sample_user_id)
        assert "Error activating user" in str(exc_info.value)
