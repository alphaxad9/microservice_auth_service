# tests/application/user/test_usecases.py

import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4, UUID
from typing import Optional

from src.application.user.usecases import UserUseCase
from src.application.user.dtos import UserDTO
from src.application.user.services import UserQueryServiceImpl, UserCommandServiceImpl
from src.domain.user.models import DomainUser
from src.domain.user.events import (
    UserCreated, UserActivated, UserDeactivated, 
    UserLoggedIn, UserLoggedOut, UserUpdated
)
from src.domain.user.exceptions import (
    UserNotFoundError, UserNotActiveError, UserDomainError
)
from src.domain.outbox.events import OutboxEvent


class TestUserUseCase:
    """Test suite for UserUseCase class."""

    @pytest.fixture
    def mock_user_query_service(self):
        return Mock(spec=UserQueryServiceImpl)

    @pytest.fixture
    def mock_user_command_service(self):
        return Mock(spec=UserCommandServiceImpl)

    @pytest.fixture
    def mock_outbox_repo(self):
        return Mock()

    @pytest.fixture
    def user_usecase(self, mock_user_query_service, mock_user_command_service, mock_outbox_repo):
        return UserUseCase(
            user_query_service=mock_user_query_service,
            user_command_service=mock_user_command_service,
            outbox_repo=mock_outbox_repo
        )

    @pytest.fixture
    def sample_user_id(self):
        return uuid4()

    @pytest.fixture
    def sample_domain_user(self, sample_user_id):
        return DomainUser(
            user_id=sample_user_id,
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )

    @pytest.fixture
    def sample_user_dto(self, sample_domain_user):
        return UserDTO.from_domain(sample_domain_user)

    # Helper method to compare DTOs by value instead of reference
    def assert_dto_equal(self, dto1, dto2):
        """Compare two UserDTO objects by their attribute values."""
        assert dto1.user_id == dto2.user_id
        assert dto1.username == dto2.username
        assert dto1.email == dto2.email
        assert dto1.first_name == dto2.first_name
        assert dto1.last_name == dto2.last_name
        assert dto1.profile_picture == dto2.profile_picture
        assert dto1.is_active == dto2.is_active
        assert dto1.is_deleted == dto2.is_deleted

    # =========================
    # COMMAND USE CASES TESTS
    # =========================

    @patch('src.application.user.usecases.NotificationBroadcaster')
    def test_publish_user_created_event_success(
        self, mock_broadcaster, user_usecase, mock_user_query_service, mock_outbox_repo, 
        sample_user_id, sample_domain_user, sample_user_dto
    ):
        # Arrange
        mock_user_query_service.get_by_id.return_value = sample_domain_user
        mock_broadcaster.return_value.send_to_user.return_value = None
        
        # Act
        result = user_usecase.publish_user_created_event(sample_user_id)
        
        # Assert
        mock_user_query_service.get_by_id.assert_called_once_with(sample_user_id)
        mock_outbox_repo.save.assert_called_once()
        
        saved_outbox_event = mock_outbox_repo.save.call_args[0][0]
        assert isinstance(saved_outbox_event, OutboxEvent)
        assert saved_outbox_event.event_type == "user.created"
        assert saved_outbox_event.aggregate_id == sample_user_id
        self.assert_dto_equal(result, sample_user_dto)

    def test_publish_user_created_event_user_not_found(
        self, user_usecase, mock_user_query_service, sample_user_id
    ):
        # Arrange
        mock_user_query_service.get_by_id.side_effect = UserNotFoundError()
        
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            user_usecase.publish_user_created_event(sample_user_id)

    def test_publish_user_created_event_general_error(
        self, user_usecase, mock_user_query_service, sample_user_id
    ):
        # Arrange
        mock_user_query_service.get_by_id.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(UserDomainError, match="Failed to publish user creation event"):
            user_usecase.publish_user_created_event(sample_user_id)

    def test_activate_user_success(
        self, user_usecase, mock_user_command_service, mock_outbox_repo,
        sample_user_id, sample_domain_user, sample_user_dto
    ):
        # Arrange
        mock_user_command_service.activate_user.return_value = sample_domain_user
        
        # Act
        result = user_usecase.activate_user(sample_user_id)
        
        # Assert
        mock_user_command_service.activate_user.assert_called_once_with(sample_user_id)
        mock_outbox_repo.save.assert_called_once()
        
        saved_outbox_event = mock_outbox_repo.save.call_args[0][0]
        assert saved_outbox_event.event_type == "user.activated"
        self.assert_dto_equal(result, sample_user_dto)

    def test_deactivate_user_success(
        self, user_usecase, mock_user_command_service, mock_outbox_repo,
        sample_user_id, sample_domain_user, sample_user_dto
    ):
        # Arrange
        mock_user_command_service.deactivate_user.return_value = sample_domain_user
        
        # Act
        result = user_usecase.deactivate_user(sample_user_id)
        
        # Assert
        mock_user_command_service.deactivate_user.assert_called_once_with(sample_user_id)
        mock_outbox_repo.save.assert_called_once()
        
        saved_outbox_event = mock_outbox_repo.save.call_args[0][0]
        assert saved_outbox_event.event_type == "user.deactivated"
        self.assert_dto_equal(result, sample_user_dto)

    def test_soft_delete_user_success(
        self, user_usecase, mock_user_command_service, mock_outbox_repo,
        sample_user_id, sample_domain_user, sample_user_dto
    ):
        # Arrange
        mock_user_command_service.soft_delete_user.return_value = sample_domain_user
        
        # Act
        result = user_usecase.soft_delete_user(sample_user_id)
        
        # Assert
        mock_user_command_service.soft_delete_user.assert_called_once_with(sample_user_id)
        mock_outbox_repo.save.assert_called_once()
        
        saved_outbox_event = mock_outbox_repo.save.call_args[0][0]
        assert saved_outbox_event.event_type == "user.soft_deleted"  # Updated to match UserSoftDeleted event
        self.assert_dto_equal(result, sample_user_dto)
    def test_hard_delete_user_success(
        self, user_usecase, mock_user_command_service, sample_user_id
    ):
        # Act
        user_usecase.hard_delete_user(sample_user_id)
        
        # Assert
        mock_user_command_service.hard_delete_user.assert_called_once_with(sample_user_id)

    def test_update_user_profile_success_with_changes(
        self, user_usecase, mock_user_query_service, mock_user_command_service, 
        mock_outbox_repo, sample_user_id, sample_domain_user
    ):
        # Arrange
        current_user = sample_domain_user
        updated_user = DomainUser(
            user_id=sample_user_id,
            username="testuser",
            email="test@example.com",
            first_name="Updated",
            last_name="User"
        )
        
        mock_user_query_service.get_by_id.return_value = current_user
        mock_user_command_service.update_user_profile.return_value = updated_user
        
        # Act
        result = user_usecase.update_user_profile(
            sample_user_id, 
            first_name="Updated", 
            last_name="User"
        )
        
        # Assert
        mock_user_query_service.get_by_id.assert_called_once_with(sample_user_id)
        # Use assert_called_with instead of assert_called_once_with for keyword arguments
        mock_user_command_service.update_user_profile.assert_called_with(
            user_id=sample_user_id, first_name="Updated", last_name="User", profile_picture=None
        )
        mock_outbox_repo.save.assert_called_once()
        
        saved_outbox_event = mock_outbox_repo.save.call_args[0][0]
        assert saved_outbox_event.event_type == "user.updated"  # Updated to match UserUpdated event
        self.assert_dto_equal(result, UserDTO.from_domain(updated_user))
    def test_update_user_profile_success_no_changes(
        self, user_usecase, mock_user_query_service, mock_user_command_service, 
        mock_outbox_repo, sample_user_id, sample_domain_user, sample_user_dto
    ):
        # Arrange
        mock_user_query_service.get_by_id.return_value = sample_domain_user
        mock_user_command_service.update_user_profile.return_value = sample_domain_user
        
        # Act - updating with same values
        result = user_usecase.update_user_profile(
            sample_user_id, 
            first_name="Test",  # Same as current
            last_name="User"    # Same as current
        )
        
        # Assert
        mock_user_query_service.get_by_id.assert_called_once_with(sample_user_id)
        assert mock_user_command_service.update_user_profile.called
        mock_outbox_repo.save.assert_not_called()  # No event should be published
        self.assert_dto_equal(result, sample_user_dto)

    def test_toggle_user_active_status_to_active(
        self, user_usecase, mock_user_command_service, mock_outbox_repo,
        sample_user_id
    ):
        # Arrange
        active_user = DomainUser(
            user_id=sample_user_id,
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        mock_user_command_service.toggle_user_active_status.return_value = active_user
        
        # Act
        result = user_usecase.toggle_user_active_status(sample_user_id)
        
        # Assert
        mock_user_command_service.toggle_user_active_status.assert_called_once_with(sample_user_id)
        mock_outbox_repo.save.assert_called_once()
        
        saved_outbox_event = mock_outbox_repo.save.call_args[0][0]
        assert saved_outbox_event.event_type == "user.activated"  # Should publish activated event
        self.assert_dto_equal(result, UserDTO.from_domain(active_user))

    def test_toggle_user_active_status_to_inactive(
        self, user_usecase, mock_user_command_service, mock_outbox_repo,
        sample_user_id
    ):
        # Arrange
        inactive_user = DomainUser(
            user_id=sample_user_id,
            username="testuser",
            email="test@example.com",
            is_active=False
        )
        mock_user_command_service.toggle_user_active_status.return_value = inactive_user
        
        # Act
        result = user_usecase.toggle_user_active_status(sample_user_id)
        
        # Assert
        saved_outbox_event = mock_outbox_repo.save.call_args[0][0]
        assert saved_outbox_event.event_type == "user.deactivated"  # Should publish deactivated event
        self.assert_dto_equal(result, UserDTO.from_domain(inactive_user))

    def test_log_user_in_success(
        self, user_usecase, mock_user_query_service, mock_outbox_repo, sample_user_id
    ):
        # Arrange
        active_user = DomainUser(
            user_id=sample_user_id,
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        mock_user_query_service.get_by_id.return_value = active_user
        
        # Act
        user_usecase.log_user_in(sample_user_id, "192.168.1.1", "Test Browser")
        
        # Assert
        mock_user_query_service.get_by_id.assert_called_once_with(sample_user_id)
        mock_outbox_repo.save.assert_called_once()
        
        saved_outbox_event = mock_outbox_repo.save.call_args[0][0]
        assert saved_outbox_event.event_type == "user.logged_in"

    def test_log_user_in_user_not_active(
        self, user_usecase, mock_user_query_service, sample_user_id
    ):
        # Arrange
        inactive_user = DomainUser(
            user_id=sample_user_id,
            username="testuser",
            email="test@example.com",
            is_active=False
        )
        mock_user_query_service.get_by_id.return_value = inactive_user
        
        # Act & Assert
        with pytest.raises(UserNotActiveError):
            user_usecase.log_user_in(sample_user_id)

    def test_log_user_out_success(
        self, user_usecase, mock_outbox_repo, sample_user_id
    ):
        # Act
        user_usecase.log_user_out(sample_user_id, "192.168.1.1", "Test Browser")
        
        # Assert
        mock_outbox_repo.save.assert_called_once()
        
        saved_outbox_event = mock_outbox_repo.save.call_args[0][0]
        assert saved_outbox_event.event_type == "user.logged_out"

    # ========================
    # QUERY USE CASES TESTS
    # ========================

    def test_get_by_id_success(
        self, user_usecase, mock_user_query_service, sample_user_id, sample_domain_user
    ):
        # Arrange
        mock_user_query_service.get_by_id.return_value = sample_domain_user
        
        # Act
        result = user_usecase.get_by_id(sample_user_id)
        
        # Assert
        # Updated to match the new default parameter include_deleted=True
        mock_user_query_service.get_by_id.assert_called_once_with(sample_user_id, True)
        self.assert_dto_equal(result, UserDTO.from_domain(sample_domain_user))

    def test_get_by_id_not_found(
        self, user_usecase, mock_user_query_service, sample_user_id
    ):
        # Arrange
        mock_user_query_service.get_by_id.side_effect = UserNotFoundError()
        
        # Act
        result = user_usecase.get_by_id(sample_user_id)
        
        # Assert
        assert result is None

    def test_get_by_email_success(
        self, user_usecase, mock_user_query_service, sample_domain_user
    ):
        # Arrange
        email = "test@example.com"
        mock_user_query_service.get_by_email.return_value = sample_domain_user
        
        # Act
        result = user_usecase.get_by_email(email)
        
        # Assert
        mock_user_query_service.get_by_email.assert_called_once_with(email)
        self.assert_dto_equal(result, UserDTO.from_domain(sample_domain_user))

    def test_get_by_username_success(
        self, user_usecase, mock_user_query_service, sample_domain_user
    ):
        # Arrange
        username = "testuser"
        mock_user_query_service.get_by_username.return_value = sample_domain_user
        
        # Act
        result = user_usecase.get_by_username(username)
        
        # Assert
        mock_user_query_service.get_by_username.assert_called_once_with(username)
        self.assert_dto_equal(result, UserDTO.from_domain(sample_domain_user))

    def test_user_exists_by_email(
        self, user_usecase, mock_user_query_service
    ):
        # Arrange
        email = "test@example.com"
        mock_user_query_service.user_exists_by_email.return_value = True
        
        # Act
        result = user_usecase.user_exists_by_email(email)
        
        # Assert
        mock_user_query_service.user_exists_by_email.assert_called_once_with(email)
        assert result is True

    def test_user_exists_by_username(
        self, user_usecase, mock_user_query_service
    ):
        # Arrange
        username = "testuser"
        mock_user_query_service.user_exists_by_username.return_value = True
        
        # Act
        result = user_usecase.user_exists_by_username(username)
        
        # Assert
        mock_user_query_service.user_exists_by_username.assert_called_once_with(username)
        assert result is True

    def test_list_all_users_success(
        self, user_usecase, mock_user_query_service, sample_domain_user
    ):
        # Arrange
        users_list = [sample_domain_user]
        mock_user_query_service.list_all_users.return_value = users_list
        
        # Act
        result = user_usecase.list_all_users(limit=10, offset=0, include_deleted=True)
        
        # Assert
        mock_user_query_service.list_all_users.assert_called_once_with(
            limit=10, offset=0, include_deleted=True
        )
        assert len(result) == 1
        self.assert_dto_equal(result[0], UserDTO.from_domain(sample_domain_user))

    def test_list_all_users_with_validation(
        self, user_usecase, mock_user_query_service, sample_domain_user
    ):
        # Arrange
        users_list = [sample_domain_user]
        mock_user_query_service.list_all_users.return_value = users_list
        
        # Act - test limit validation
        result = user_usecase.list_all_users(limit=1500, offset=-5)
        
        # Assert - should be normalized to max values
        mock_user_query_service.list_all_users.assert_called_once_with(
            limit=1000, offset=0, include_deleted=False
        )

    def test_search_users_success(
        self, user_usecase, mock_user_query_service, sample_domain_user
    ):
        # Arrange
        query = "test"
        users_list = [sample_domain_user]
        mock_user_query_service.search_users.return_value = users_list
        
        # Act
        result = user_usecase.search_users(query, limit=10)
        
        # Assert
        mock_user_query_service.search_users.assert_called_once_with(query=query, limit=10)
        assert len(result) == 1
        self.assert_dto_equal(result[0], UserDTO.from_domain(sample_domain_user))

    def test_is_user_active_true(
        self, user_usecase, mock_user_query_service, sample_user_id
    ):
        # Arrange
        active_user = DomainUser(
            user_id=sample_user_id,
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        mock_user_query_service.get_by_id.return_value = active_user
        
        # Act
        result = user_usecase.is_user_active(sample_user_id)
        
        # Assert
        assert result is True

    def test_is_user_active_false(
        self, user_usecase, mock_user_query_service, sample_user_id
    ):
        # Arrange
        mock_user_query_service.get_by_id.side_effect = UserNotFoundError()
        
        # Act
        result = user_usecase.is_user_active(sample_user_id)
        
        # Assert
        assert result is False

    def test_is_user_soft_deleted_true(
        self, user_usecase, mock_user_query_service, sample_user_id
    ):
        # Arrange
        mock_user_query_service.is_user_soft_deleted.return_value = True
        
        # Act
        result = user_usecase.is_user_soft_deleted(sample_user_id)
        
        # Assert
        mock_user_query_service.is_user_soft_deleted.assert_called_once_with(sample_user_id)
        assert result is True

    def test_is_user_soft_deleted_false(
        self, user_usecase, mock_user_query_service, sample_user_id
    ):
        # Arrange
        mock_user_query_service.is_user_soft_deleted.return_value = False
        
        # Act
        result = user_usecase.is_user_soft_deleted(sample_user_id)
        
        # Assert
        assert result is False

    # ========================
    # ERROR HANDLING TESTS
    # ========================

    def test_command_operations_propagate_user_not_found_error(
        self, user_usecase, mock_user_command_service, sample_user_id
    ):
        # Test that UserNotFoundError is propagated for all command operations
        operations = [
            lambda: user_usecase.activate_user(sample_user_id),
            lambda: user_usecase.deactivate_user(sample_user_id),
            lambda: user_usecase.soft_delete_user(sample_user_id),
            lambda: user_usecase.hard_delete_user(sample_user_id),
            lambda: user_usecase.toggle_user_active_status(sample_user_id),
        ]
        
        for operation in operations:
            mock_user_command_service.reset_mock()
            mock_user_command_service.activate_user.side_effect = UserNotFoundError()
            mock_user_command_service.deactivate_user.side_effect = UserNotFoundError()
            mock_user_command_service.soft_delete_user.side_effect = UserNotFoundError()
            mock_user_command_service.hard_delete_user.side_effect = UserNotFoundError()
            mock_user_command_service.toggle_user_active_status.side_effect = UserNotFoundError()
            
            with pytest.raises(UserNotFoundError):
                operation()

    def test_command_operations_wrap_general_errors(
        self, user_usecase, mock_user_command_service, sample_user_id
    ):
        # Test that general errors are wrapped in UserDomainError
        operations = [
            lambda: user_usecase.activate_user(sample_user_id),
            lambda: user_usecase.deactivate_user(sample_user_id),
        ]
        
        for operation in operations:
            mock_user_command_service.reset_mock()
            mock_user_command_service.activate_user.side_effect = Exception("DB error")
            mock_user_command_service.deactivate_user.side_effect = Exception("DB error")
            
            with pytest.raises(UserDomainError, match="Failed to"):
                operation()

    @patch('src.application.user.usecases.NotificationBroadcaster')
    def test_websocket_notification_failure_does_not_break_operation(
        self, mock_broadcaster, user_usecase, mock_user_query_service, 
        mock_outbox_repo, sample_user_id, sample_domain_user
    ):
        # Arrange
        mock_user_query_service.get_by_id.return_value = sample_domain_user
        mock_broadcaster.return_value.send_to_user.side_effect = Exception("WebSocket error")
        
        # Act - Should not raise despite WebSocket failure
        result = user_usecase.publish_user_created_event(sample_user_id)
        
        # Assert - Operation should complete successfully
        self.assert_dto_equal(result, UserDTO.from_domain(sample_domain_user))
        mock_outbox_repo.save.assert_called_once()  # Event should still be saved