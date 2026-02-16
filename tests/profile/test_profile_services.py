from __future__ import annotations
from unittest.mock import Mock, MagicMock
import pytest
from uuid import UUID, uuid4

from src.domain.profile.models import PrimaryProfile
from src.domain.profile.exceptions import (
    ProfileNotFoundError,
    ProfileAlreadyExistsError,
    ProfileDomainError,
    InvalidDeltaError
)
from src.application.profile.services import (
    PrimaryProfileQueryServiceImpl,
    PrimaryProfileCommandServiceImpl
)


@pytest.fixture
def mock_profile_repo():
    return Mock()

@pytest.fixture
def mock_profile_query_service():
    return Mock()

@pytest.fixture
def sample_profile():
    return PrimaryProfile(
        user_id=uuid4(),
        followers_count=10,
        following_count=5,
        unread_notifications_count=2,
        bio="Hello world",
        account_type="public"
    )


# ========================================
# PrimaryProfileQueryServiceImpl Tests
# ========================================

class TestPrimaryProfileQueryServiceImpl:

    def test_get_by_user_id_success(self, mock_profile_repo, sample_profile):
        # Arrange
        mock_profile_repo.get_by_user_id.return_value = sample_profile
        service = PrimaryProfileQueryServiceImpl(mock_profile_repo)

        # Act
        result = service.get_by_user_id(sample_profile.user_id)

        # Assert
        assert result == sample_profile
        mock_profile_repo.get_by_user_id.assert_called_once_with(sample_profile.user_id)

    def test_get_by_user_id_not_found(self, mock_profile_repo, sample_profile):
        # Arrange
        mock_profile_repo.get_by_user_id.side_effect = ProfileNotFoundError(str(sample_profile.user_id))
        service = PrimaryProfileQueryServiceImpl(mock_profile_repo)

        # Act & Assert
        with pytest.raises(ProfileNotFoundError):
            service.get_by_user_id(sample_profile.user_id)
        mock_profile_repo.get_by_user_id.assert_called_once_with(sample_profile.user_id)

    def test_get_by_user_id_unexpected_error(self, mock_profile_repo, sample_profile):
        # Arrange
        mock_profile_repo.get_by_user_id.side_effect = RuntimeError("DB down")
        service = PrimaryProfileQueryServiceImpl(mock_profile_repo)

        # Act & Assert
        with pytest.raises(ProfileDomainError, match="Error retrieving profile by user ID"):
            service.get_by_user_id(sample_profile.user_id)

    def test_exists_for_user_success(self, mock_profile_repo, sample_profile):
        # Arrange
        mock_profile_repo.exists_for_user.return_value = True
        service = PrimaryProfileQueryServiceImpl(mock_profile_repo)

        # Act
        result = service.exists_for_user(sample_profile.user_id)

        # Assert
        assert result is True
        mock_profile_repo.exists_for_user.assert_called_once_with(sample_profile.user_id)

    def test_exists_for_user_error(self, mock_profile_repo, sample_profile):
        # Arrange
        mock_profile_repo.exists_for_user.side_effect = RuntimeError("DB down")
        service = PrimaryProfileQueryServiceImpl(mock_profile_repo)

        # Act & Assert
        with pytest.raises(ProfileDomainError, match="Error checking profile existence"):
            service.exists_for_user(sample_profile.user_id)

    @pytest.mark.parametrize("sort_by", ["followers", "following"])
    def test_list_top_profiles_valid_sort(self, mock_profile_repo, sample_profile, sort_by):
        # Arrange
        mock_profile_repo.list_top_profiles.return_value = [sample_profile]
        service = PrimaryProfileQueryServiceImpl(mock_profile_repo)

        # Act
        result = service.list_top_profiles(by=sort_by, limit=10, offset=0)

        # Assert
        assert result == [sample_profile]
        mock_profile_repo.list_top_profiles.assert_called_once_with(by=sort_by, limit=10, offset=0)

    def test_list_top_profiles_invalid_sort(self, mock_profile_repo):
        # Arrange
        service = PrimaryProfileQueryServiceImpl(mock_profile_repo)

        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported sort field: invalid"):
            service.list_top_profiles(by="invalid")

    def test_list_top_profiles_repo_error(self, mock_profile_repo):
        # Arrange
        mock_profile_repo.list_top_profiles.side_effect = RuntimeError("DB down")
        service = PrimaryProfileQueryServiceImpl(mock_profile_repo)

        # Act & Assert
        with pytest.raises(ProfileDomainError, match="Error listing top profiles"):
            service.list_top_profiles(by="followers")


# ========================================
# PrimaryProfileCommandServiceImpl Tests
# ========================================

class TestPrimaryProfileCommandServiceImpl:

    def test_create_profile_success(self, mock_profile_repo, mock_profile_query_service, sample_profile):
        # Arrange
        mock_profile_query_service.exists_for_user.return_value = False
        mock_profile_repo.create.return_value = sample_profile
        service = PrimaryProfileCommandServiceImpl(mock_profile_repo, mock_profile_query_service)

        # Act
        result = service.create_profile(sample_profile)

        # Assert
        assert result == sample_profile
        mock_profile_query_service.exists_for_user.assert_called_once_with(sample_profile.user_id)
        mock_profile_repo.create.assert_called_once_with(sample_profile)

    def test_create_profile_already_exists(self, mock_profile_repo, mock_profile_query_service, sample_profile):
        # Arrange
        mock_profile_query_service.exists_for_user.return_value = True
        service = PrimaryProfileCommandServiceImpl(mock_profile_repo, mock_profile_query_service)

        # Act & Assert
        with pytest.raises(ProfileAlreadyExistsError):
            service.create_profile(sample_profile)
        mock_profile_query_service.exists_for_user.assert_called_once_with(sample_profile.user_id)
        mock_profile_repo.create.assert_not_called()

    def test_create_profile_unexpected_error(self, mock_profile_repo, mock_profile_query_service, sample_profile):
        # Arrange
        mock_profile_query_service.exists_for_user.return_value = False
        mock_profile_repo.create.side_effect = RuntimeError("DB down")
        service = PrimaryProfileCommandServiceImpl(mock_profile_repo, mock_profile_query_service)

        # Act & Assert
        with pytest.raises(ProfileDomainError, match="Error creating profile"):
            service.create_profile(sample_profile)

    def test_update_profile_success(self, mock_profile_repo, mock_profile_query_service, sample_profile):
        # Arrange
        mock_profile_query_service.get_by_user_id.return_value = sample_profile
        mock_profile_repo.update.return_value = sample_profile
        service = PrimaryProfileCommandServiceImpl(mock_profile_repo, mock_profile_query_service)

        # Act
        result = service.update_profile(sample_profile)

        # Assert
        assert result == sample_profile
        mock_profile_query_service.get_by_user_id.assert_called_once_with(sample_profile.user_id)
        mock_profile_repo.update.assert_called_once_with(sample_profile)

    def test_update_profile_not_found(self, mock_profile_repo, mock_profile_query_service, sample_profile):
        # Arrange
        mock_profile_query_service.get_by_user_id.side_effect = ProfileNotFoundError(str(sample_profile.user_id))
        service = PrimaryProfileCommandServiceImpl(mock_profile_repo, mock_profile_query_service)

        # Act & Assert
        with pytest.raises(ProfileNotFoundError):
            service.update_profile(sample_profile)

    @pytest.mark.parametrize("method_name,delta_arg", [
        ("increment_followers", 1),
        ("decrement_followers", 1),
        ("increment_following", 1),
        ("decrement_following", 1),
        ("increment_unread_notifications", 1),
        ("decrement_unread_notifications", 1),
    ])
    def test_increment_decrement_methods_success(self, mock_profile_repo, mock_profile_query_service, sample_profile, method_name, delta_arg):
        # Arrange
        mock_profile_repo_method = getattr(mock_profile_repo, method_name)
        mock_profile_repo_method.return_value = sample_profile
        service = PrimaryProfileCommandServiceImpl(mock_profile_repo, mock_profile_query_service)
        service_method = getattr(service, method_name)

        # Act
        result = service_method(sample_profile.user_id, delta=delta_arg)

        # Assert
        assert result == sample_profile
        mock_profile_repo_method.assert_called_once_with(sample_profile.user_id, delta_arg)

    @pytest.mark.parametrize("method_name", [
        "increment_followers",
        "decrement_followers",
        "increment_following",
        "decrement_following",
        "increment_unread_notifications",
        "decrement_unread_notifications",
    ])
    @pytest.mark.parametrize("invalid_delta", [0, -1, -5])
    def test_increment_decrement_methods_invalid_delta(self, mock_profile_repo, mock_profile_query_service, sample_profile, method_name, invalid_delta):
        # Arrange
        service = PrimaryProfileCommandServiceImpl(mock_profile_repo, mock_profile_query_service)
        service_method = getattr(service, method_name)

        # Act & Assert
        with pytest.raises(InvalidDeltaError):
            service_method(sample_profile.user_id, delta=invalid_delta)

    @pytest.mark.parametrize("method_name", [
        "increment_followers",
        "decrement_followers",
        "increment_following",
        "decrement_following",
        "increment_unread_notifications",
        "decrement_unread_notifications",
        "clear_unread_notifications",
        "mark_online",
    ])
    def test_methods_profile_not_found(self, mock_profile_repo, mock_profile_query_service, sample_profile, method_name):
        # Arrange
        mock_repo_method = getattr(mock_profile_repo, method_name)
        mock_repo_method.side_effect = ProfileNotFoundError(str(sample_profile.user_id))
        service = PrimaryProfileCommandServiceImpl(mock_profile_repo, mock_profile_query_service)
        service_method = getattr(service, method_name)
        args = [sample_profile.user_id]
        if method_name in [
            "increment_followers", "decrement_followers",
            "increment_following", "decrement_following",
            "increment_unread_notifications", "decrement_unread_notifications"
        ]:
            args.append(1)

        # Act & Assert
        with pytest.raises(ProfileNotFoundError):
            service_method(*args)

    def test_clear_unread_notifications_success(self, mock_profile_repo, mock_profile_query_service, sample_profile):
        # Arrange
        mock_profile_repo.clear_unread_notifications.return_value = sample_profile
        service = PrimaryProfileCommandServiceImpl(mock_profile_repo, mock_profile_query_service)

        # Act
        result = service.clear_unread_notifications(sample_profile.user_id)

        # Assert
        assert result == sample_profile
        mock_profile_repo.clear_unread_notifications.assert_called_once_with(sample_profile.user_id)

    def test_mark_online_success(self, mock_profile_repo, mock_profile_query_service, sample_profile):
        # Arrange
        mock_profile_repo.mark_online.return_value = sample_profile
        service = PrimaryProfileCommandServiceImpl(mock_profile_repo, mock_profile_query_service)

        # Act
        result = service.mark_online(sample_profile.user_id)

        # Assert
        assert result == sample_profile
        mock_profile_repo.mark_online.assert_called_once_with(sample_profile.user_id)

    def test_toggle_deleted_success(self, mock_profile_repo, mock_profile_query_service, sample_profile):
        # Arrange
        mock_profile_query_service.get_by_user_id.return_value = sample_profile
        mock_profile_repo.update.return_value = sample_profile
        original_deleted = sample_profile.is_deleted
        service = PrimaryProfileCommandServiceImpl(mock_profile_repo, mock_profile_query_service)

        # Act
        result = service.toggle_deleted(sample_profile.user_id)

        # Assert
        assert result == sample_profile
        assert sample_profile.is_deleted != original_deleted
        mock_profile_query_service.get_by_user_id.assert_called_once_with(sample_profile.user_id)
        mock_profile_repo.update.assert_called_once_with(sample_profile)
        
    def test_toggle_deleted_not_found(self, mock_profile_repo, mock_profile_query_service, sample_profile):
        # Arrange
        mock_profile_query_service.get_by_user_id.side_effect = ProfileNotFoundError(str(sample_profile.user_id))
        service = PrimaryProfileCommandServiceImpl(mock_profile_repo, mock_profile_query_service)

        # Act & Assert
        with pytest.raises(ProfileNotFoundError):
            service.toggle_deleted(sample_profile.user_id)

    def test_delete_permanently_success(self, mock_profile_repo, mock_profile_query_service, sample_profile):
        # Arrange
        mock_profile_query_service.get_by_user_id.return_value = sample_profile
        service = PrimaryProfileCommandServiceImpl(mock_profile_repo, mock_profile_query_service)

        # Act
        service.delete_permanently(sample_profile.user_id)

        # Assert
        mock_profile_query_service.get_by_user_id.assert_called_once_with(sample_profile.user_id)
        mock_profile_repo.delete_permanently.assert_called_once_with(sample_profile.user_id)

    def test_delete_permanently_not_found(self, mock_profile_repo, mock_profile_query_service, sample_profile):
        # Arrange
        mock_profile_query_service.get_by_user_id.side_effect = ProfileNotFoundError(str(sample_profile.user_id))
        service = PrimaryProfileCommandServiceImpl(mock_profile_repo, mock_profile_query_service)

        # Act & Assert
        with pytest.raises(ProfileNotFoundError):
            service.delete_permanently(sample_profile.user_id)