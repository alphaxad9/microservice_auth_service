from __future__ import annotations
from unittest.mock import Mock
from uuid import UUID, uuid4
from datetime import date
import pytest
from typing import Sequence, List
from src.application.profile.usecases import ProfileUseCase
from src.domain.user.exceptions import UserNotFoundError
from src.domain.profile.exceptions import (
    ProfileNotFoundError,
    ProfileAlreadyExistsError,
    ProfileDomainError,
    InvalidProfileUpdateError, InvalidDeltaError
)
from src.domain.profile.models import PrimaryProfile
from src.application.profile.dtos import MyUserProfileDTO, ForeignUserProfileDTO


def _make_domain_user(user_id: UUID, is_deleted: bool = False):
    """Helper to create a consistent mock user."""
    user = Mock()
    user.user_id = user_id
    user.is_deleted = is_deleted
    user.first_name = "John"
    user.last_name = "Doe"
    user.email = "john@example.com"
    user.is_active = True
    return user


# ========================
# CREATE PROFILE TESTS
# ========================

def test_create_profile_success():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    mock_profile_query_service.exists_for_user.return_value = False

    mock_profile_command_service = Mock()
    mock_profile_command_service.create_profile.return_value = PrimaryProfile(user_id=user_id)

    mock_outbox_repo = Mock()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=mock_profile_command_service,
        outbox_repo=mock_outbox_repo,
    )

    result = use_case.create_profile(user_id)

    assert isinstance(result, MyUserProfileDTO)
    assert result.user_id == user_id
    mock_profile_query_service.exists_for_user.assert_called_once_with(user_id)
    mock_profile_command_service.create_profile.assert_called_once()
    mock_outbox_repo.save.assert_called_once()


def test_create_profile_already_exists():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    mock_profile_query_service.exists_for_user.return_value = True
    mock_profile_query_service.get_by_user_id.return_value = PrimaryProfile(user_id=user_id)

    mock_profile_command_service = Mock()
    mock_outbox_repo = Mock()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=mock_profile_command_service,
        outbox_repo=mock_outbox_repo,
    )

    result = use_case.create_profile(user_id)

    assert result.user_id == user_id
    mock_profile_command_service.create_profile.assert_not_called()
    mock_outbox_repo.save.assert_not_called()


def test_create_profile_race_condition_fallback():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    mock_profile_query_service.exists_for_user.return_value = False
    mock_profile_query_service.get_by_user_id.return_value = PrimaryProfile(user_id=user_id)

    mock_profile_command_service = Mock()
    mock_profile_command_service.create_profile.side_effect = ProfileAlreadyExistsError(user_id=str(user_id))

    mock_outbox_repo = Mock()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=mock_profile_command_service,
        outbox_repo=mock_outbox_repo,
    )

    result = use_case.create_profile(user_id)

    assert result.user_id == user_id
    mock_profile_command_service.create_profile.assert_called_once()
    mock_outbox_repo.save.assert_not_called()


def test_create_profile_user_not_found():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.side_effect = UserNotFoundError()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=Mock(),
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    # ⚠️ IMPORTANT: Your use case must re-raise UserNotFoundError!
    # Add `UserNotFoundError` to the re-raised exceptions in `create_profile`.
    with pytest.raises(UserNotFoundError):
        use_case.create_profile(user_id)


def test_create_profile_user_soft_deleted():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id, is_deleted=True)

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=Mock(),
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    with pytest.raises(ProfileDomainError, match="Cannot create profile for soft-deleted user"):
        use_case.create_profile(user_id)


def test_create_profile_unexpected_error():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    mock_profile_query_service.exists_for_user.side_effect = RuntimeError("DB down")

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    with pytest.raises(ProfileDomainError, match="Failed to create profile"):
        use_case.create_profile(user_id)


# ========================
# UPDATE PROFILE TESTS
# ========================

def test_update_profile_success():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    current_profile = PrimaryProfile(user_id=user_id)
    mock_profile_query_service.get_by_user_id.return_value = current_profile

    mock_profile_command_service = Mock()
    updated_profile = PrimaryProfile(user_id=user_id, bio="New bio")
    mock_profile_command_service.update_profile.return_value = updated_profile

    mock_outbox_repo = Mock()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=mock_profile_command_service,
        outbox_repo=mock_outbox_repo,
    )

    result = use_case.update_profile(user_id, bio="New bio")

    assert result.bio == "New bio"
    mock_profile_command_service.update_profile.assert_called_once()
    mock_outbox_repo.save.assert_called_once()


def test_update_profile_partial_update():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    current_profile = PrimaryProfile(user_id=user_id)
    mock_profile_query_service.get_by_user_id.return_value = current_profile

    mock_profile_command_service = Mock()
    mock_profile_command_service.update_profile.return_value = current_profile

    mock_outbox_repo = Mock()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=mock_profile_command_service,
        outbox_repo=mock_outbox_repo,
    )

    result = use_case.update_profile(user_id, profession="developer", theme="dark")

    # Do NOT assert on real method calls
    mock_outbox_repo.save.assert_called_once()
    saved_event = mock_outbox_repo.save.call_args[0][0]
    assert saved_event.event_payload["payload"]["updated_fields"] == {"profession": "developer", "theme": "dark"}
    assert result.profession == "developer"
    assert result.theme == "dark"

def test_update_profile_date_of_birth_valid():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    current_profile = PrimaryProfile(user_id=user_id)
    mock_profile_query_service.get_by_user_id.return_value = current_profile

    mock_profile_command_service = Mock()
    # Return a profile with the updated dob
    updated_profile = PrimaryProfile(user_id=user_id)
    updated_profile.date_of_birth = date(1990, 5, 20)
    mock_profile_command_service.update_profile.return_value = updated_profile

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=mock_profile_command_service,
        outbox_repo=Mock(),
    )

    result = use_case.update_profile(user_id, date_of_birth="1990-05-20")

    assert result.date_of_birth == date(1990, 5, 20)
def test_update_profile_date_of_birth_invalid():
    user_id = uuid4()
    mock_profile_query_service = Mock()
    mock_profile_query_service.get_by_user_id.return_value = PrimaryProfile(user_id=user_id)

    use_case = ProfileUseCase(
        user_query_service=Mock(),
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    with pytest.raises(InvalidProfileUpdateError, match="must be a valid ISO date string"):
        use_case.update_profile(user_id, date_of_birth="not-a-date")


def test_update_profile_no_fields_provided():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    current_profile = PrimaryProfile(user_id=user_id)
    mock_profile_query_service.get_by_user_id.return_value = current_profile

    mock_profile_command_service = Mock()
    mock_outbox_repo = Mock()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=mock_profile_command_service,
        outbox_repo=mock_outbox_repo,
    )

    result = use_case.update_profile(user_id)

    assert result.user_id == user_id
    mock_profile_command_service.update_profile.assert_not_called()
    mock_outbox_repo.save.assert_not_called()


def test_update_profile_profile_not_found():
    user_id = uuid4()
    mock_profile_query_service = Mock()
    mock_profile_query_service.get_by_user_id.side_effect = ProfileNotFoundError()

    use_case = ProfileUseCase(
        user_query_service=Mock(),
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    with pytest.raises(ProfileNotFoundError):
        use_case.update_profile(user_id, bio="test")

def test_update_profile_invalid_field():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    current_profile = PrimaryProfile(user_id=user_id)
    mock_profile_query_service.get_by_user_id.return_value = current_profile

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    with pytest.raises(InvalidProfileUpdateError):
        use_case.update_profile(user_id, theme="neon-rainbow")  # invalid theme
def test_update_profile_unexpected_error():
    user_id = uuid4()
    mock_profile_query_service = Mock()
    mock_profile_query_service.get_by_user_id.side_effect = ValueError("Oops")

    use_case = ProfileUseCase(
        user_query_service=Mock(),
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    with pytest.raises(ProfileDomainError, match="Failed to update profile"):
        use_case.update_profile(user_id, bio="test")



# ==============================
# FOLLOWER / FOLLOWING TESTS
# ==============================

def test_increment_followers_success():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    current_profile = PrimaryProfile(user_id=user_id, followers_count=5)
    mock_profile_query_service.get_by_user_id.return_value = current_profile

    mock_profile_command_service = Mock()
    updated_profile = PrimaryProfile(user_id=user_id, followers_count=7)
    mock_profile_command_service.increment_followers.return_value = updated_profile

    mock_outbox_repo = Mock()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=mock_profile_command_service,
        outbox_repo=mock_outbox_repo,
    )

    result = use_case.increment_followers(user_id, delta=2)

    assert result.followers_count == 7
    mock_profile_command_service.increment_followers.assert_called_once_with(user_id, 2)
    mock_outbox_repo.save.assert_called_once()
    saved_event = mock_outbox_repo.save.call_args[0][0]
    assert saved_event.event_payload["payload"] == {"delta": 2, "new_count": 7}


def test_decrement_followers_success():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    current_profile = PrimaryProfile(user_id=user_id, followers_count=5)
    mock_profile_query_service.get_by_user_id.return_value = current_profile

    mock_profile_command_service = Mock()
    updated_profile = PrimaryProfile(user_id=user_id, followers_count=3)
    mock_profile_command_service.decrement_followers.return_value = updated_profile

    mock_outbox_repo = Mock()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=mock_profile_command_service,
        outbox_repo=mock_outbox_repo,
    )

    result = use_case.decrement_followers(user_id, delta=2)

    assert result.followers_count == 3
    mock_profile_command_service.decrement_followers.assert_called_once_with(user_id, 2)
    mock_outbox_repo.save.assert_called_once()
    saved_event = mock_outbox_repo.save.call_args[0][0]
    assert saved_event.event_payload["payload"] == {"delta": 2, "new_count": 3}


def test_increment_following_success():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    current_profile = PrimaryProfile(user_id=user_id, following_count=10)
    mock_profile_query_service.get_by_user_id.return_value = current_profile

    mock_profile_command_service = Mock()
    updated_profile = PrimaryProfile(user_id=user_id, following_count=12)
    mock_profile_command_service.increment_following.return_value = updated_profile

    mock_outbox_repo = Mock()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=mock_profile_command_service,
        outbox_repo=mock_outbox_repo,
    )

    result = use_case.increment_following(user_id, delta=2)

    assert result.following_count == 12
    mock_profile_command_service.increment_following.assert_called_once_with(user_id, 2)
    mock_outbox_repo.save.assert_called_once()
    saved_event = mock_outbox_repo.save.call_args[0][0]
    assert saved_event.event_payload["payload"] == {"delta": 2, "new_count": 12}


def test_decrement_following_success():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    current_profile = PrimaryProfile(user_id=user_id, following_count=10)
    mock_profile_query_service.get_by_user_id.return_value = current_profile

    mock_profile_command_service = Mock()
    updated_profile = PrimaryProfile(user_id=user_id, following_count=8)
    mock_profile_command_service.decrement_following.return_value = updated_profile

    mock_outbox_repo = Mock()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=mock_profile_command_service,
        outbox_repo=mock_outbox_repo,
    )

    result = use_case.decrement_following(user_id, delta=2)

    assert result.following_count == 8
    mock_profile_command_service.decrement_following.assert_called_once_with(user_id, 2)
    mock_outbox_repo.save.assert_called_once()
    saved_event = mock_outbox_repo.save.call_args[0][0]
    assert saved_event.event_payload["payload"] == {"delta": 2, "new_count": 8}


def test_increment_followers_profile_not_found():
    user_id = uuid4()
    mock_profile_query_service = Mock()
    mock_profile_query_service.get_by_user_id.side_effect = ProfileNotFoundError()

    use_case = ProfileUseCase(
        user_query_service=Mock(),
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    with pytest.raises(ProfileNotFoundError):
        use_case.increment_followers(user_id)


def test_increment_followers_invalid_delta():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    mock_profile_query_service.get_by_user_id.return_value = PrimaryProfile(user_id=user_id)

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    with pytest.raises(InvalidDeltaError):
        use_case.increment_followers(user_id, delta=0)

    with pytest.raises(InvalidDeltaError):
        use_case.increment_followers(user_id, delta=-1)


# ========================
# TOGGLE DELETED TESTS
# ========================

def test_toggle_deleted_success():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    current_profile = PrimaryProfile(user_id=user_id, is_deleted=False)
    mock_profile_query_service.get_by_user_id.return_value = current_profile

    mock_profile_command_service = Mock()
    updated_profile = PrimaryProfile(user_id=user_id, is_deleted=True)
    mock_profile_command_service.update_profile.return_value = updated_profile

    mock_outbox_repo = Mock()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=mock_profile_command_service,
        outbox_repo=mock_outbox_repo,
    )

    result = use_case.toggle_deleted(user_id)

    assert isinstance(result, MyUserProfileDTO)
    assert result.is_deleted is True
    mock_profile_command_service.update_profile.assert_called_once()
    mock_outbox_repo.save.assert_called_once()
    saved_event = mock_outbox_repo.save.call_args[0][0]
    assert saved_event.event_type == "profile.soft_deleted_toggled"
    assert saved_event.event_payload["payload"]["is_deleted"] is True


def test_toggle_deleted_user_not_found():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.side_effect = UserNotFoundError()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=Mock(),
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    with pytest.raises(UserNotFoundError):
        use_case.toggle_deleted(user_id)


def test_toggle_deleted_profile_not_found():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    mock_profile_query_service.get_by_user_id.side_effect = ProfileNotFoundError()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    with pytest.raises(ProfileNotFoundError):
        use_case.toggle_deleted(user_id)


def test_toggle_deleted_unexpected_error():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    mock_profile_query_service.get_by_user_id.side_effect = RuntimeError("DB error")

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    with pytest.raises(ProfileDomainError, match="Failed to toggle profile deletion status"):
        use_case.toggle_deleted(user_id)


# ========================
# MARK ONLINE TESTS
# ========================

def test_mark_online_success():
    user_id = uuid4()
    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    current_profile = PrimaryProfile(user_id=user_id)
    mock_profile_query_service.get_by_user_id.return_value = current_profile

    mock_profile_command_service = Mock()
    updated_profile = PrimaryProfile(user_id=user_id)
    # Simulate updated last_seen_at
    from datetime import datetime, timezone
    updated_profile.last_seen_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    mock_profile_command_service.update_profile.return_value = updated_profile

    mock_outbox_repo = Mock()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=mock_profile_command_service,
        outbox_repo=mock_outbox_repo,
    )

    result = use_case.mark_online(user_id)

    assert isinstance(result, MyUserProfileDTO)
    assert result.last_seen_at == updated_profile.last_seen_at
    mock_profile_command_service.update_profile.assert_called_once()
    mock_outbox_repo.save.assert_called_once()
    saved_event = mock_outbox_repo.save.call_args[0][0]
    assert saved_event.event_type == "profile.user_marked_online"
    assert "last_seen_at" in saved_event.event_payload["payload"]
def test_mark_online_profile_not_found():
    user_id = uuid4()
    mock_profile_query_service = Mock()
    mock_profile_query_service.get_by_user_id.side_effect = ProfileNotFoundError()

    use_case = ProfileUseCase(
        user_query_service=Mock(),
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    with pytest.raises(ProfileNotFoundError):
        use_case.mark_online(user_id)


# ========================
# GET BY USER ID TESTS
# ========================

def test_get_by_user_id_own_profile():
    user_id = uuid4()
    requester_id = user_id  # same user

    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    profile = PrimaryProfile(user_id=user_id)
    mock_profile_query_service.get_by_user_id.return_value = profile

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    result = use_case.get_by_user_id(user_id, requester_id)

    assert isinstance(result, MyUserProfileDTO)
    assert result.user_id == user_id


def test_get_by_user_id_foreign_profile():
    user_id = uuid4()
    requester_id = uuid4()  # different user

    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.return_value = _make_domain_user(user_id)

    mock_profile_query_service = Mock()
    profile = PrimaryProfile(user_id=user_id)
    mock_profile_query_service.get_by_user_id.return_value = profile

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    result = use_case.get_by_user_id(user_id, requester_id)

    assert isinstance(result, ForeignUserProfileDTO)
    assert result.user_id == user_id


def test_get_by_user_id_user_not_found():
    user_id = uuid4()
    requester_id = uuid4()

    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.side_effect = UserNotFoundError()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=Mock(),
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    with pytest.raises(UserNotFoundError):
        use_case.get_by_user_id(user_id, requester_id)


# ========================
# EXISTS FOR USER TESTS
# ========================

def test_exists_for_user_true():
    user_id = uuid4()
    mock_profile_query_service = Mock()
    mock_profile_query_service.exists_for_user.return_value = True

    use_case = ProfileUseCase(
        user_query_service=Mock(),
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    assert use_case.exists_for_user(user_id) is True


def test_exists_for_user_false():
    user_id = uuid4()
    mock_profile_query_service = Mock()
    mock_profile_query_service.exists_for_user.return_value = False

    use_case = ProfileUseCase(
        user_query_service=Mock(),
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    assert use_case.exists_for_user(user_id) is False


def test_exists_for_user_error_returns_false():
    user_id = uuid4()
    mock_profile_query_service = Mock()
    mock_profile_query_service.exists_for_user.side_effect = Exception("DB unreachable")

    use_case = ProfileUseCase(
        user_query_service=Mock(),
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    # Per implementation: suppress error and return False
    assert use_case.exists_for_user(user_id) is False


# ========================
# LIST TOP PROFILES TESTS
# ========================

def test_list_top_profiles_excludes_requester():
    requester_id = uuid4()
    other_id1 = uuid4()
    other_id2 = uuid4()

    # Mock top profiles: include requester to test filtering
    top_profiles = [
        PrimaryProfile(user_id=requester_id, followers_count=100, account_type="public"),
        PrimaryProfile(user_id=other_id1, followers_count=90, account_type="public"),
        PrimaryProfile(user_id=other_id2, followers_count=80, account_type="public"),
    ]

    mock_profile_query_service = Mock()
    mock_profile_query_service.list_top_profiles.return_value = top_profiles

    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.side_effect = lambda uid, **kw: _make_domain_user(uid)

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    result = use_case.list_top_profiles(requester_id, limit=2)

    assert len(result) == 2
    returned_ids = {dto.user_id for dto in result}
    assert requester_id not in returned_ids
    assert other_id1 in returned_ids
    assert other_id2 in returned_ids


def test_list_top_profiles_respects_public_and_not_deleted():
    requester_id = uuid4()
    private_id = uuid4()
    deleted_id = uuid4()
    public_id = uuid4()

    top_profiles = [
        PrimaryProfile(user_id=private_id, account_type="private", is_deleted=False),
        PrimaryProfile(user_id=deleted_id, account_type="public", is_deleted=True),
        PrimaryProfile(user_id=public_id, account_type="public", is_deleted=False),
    ]

    mock_profile_query_service = Mock()
    mock_profile_query_service.list_top_profiles.return_value = top_profiles

    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.side_effect = lambda uid, **kw: _make_domain_user(uid)

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    result = use_case.list_top_profiles(requester_id, limit=10)

    assert len(result) == 1
    assert result[0].user_id == public_id


def test_list_top_profiles_skips_missing_users():
    requester_id = uuid4()
    missing_user_id = uuid4()

    top_profiles = [
        PrimaryProfile(user_id=missing_user_id, account_type="public", is_deleted=False),
    ]

    mock_profile_query_service = Mock()
    mock_profile_query_service.list_top_profiles.return_value = top_profiles

    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.side_effect = UserNotFoundError()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    result = use_case.list_top_profiles(requester_id, limit=10)

    assert len(result) == 0  # skipped missing user


def test_list_top_profiles_error_raises_domain_error():
    requester_id = uuid4()
    mock_profile_query_service = Mock()
    mock_profile_query_service.list_top_profiles.side_effect = ValueError("Invalid query")

    use_case = ProfileUseCase(
        user_query_service=Mock(),
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    with pytest.raises(ProfileDomainError, match="Failed to list top profiles"):
        use_case.list_top_profiles(requester_id)





# ========================
# LIST ALL PROFILES TESTS
# ========================

def test_list_all_profiles_excludes_requester():
    requester_id = uuid4()
    other_id1 = uuid4()
    other_id2 = uuid4()

    # Mock all profiles: include requester to test filtering
    all_profiles = [
        PrimaryProfile(user_id=requester_id, account_type="public", is_deleted=False),
        PrimaryProfile(user_id=other_id1, account_type="public", is_deleted=False),
        PrimaryProfile(user_id=other_id2, account_type="public", is_deleted=False),
    ]

    mock_profile_query_service = Mock()
    mock_profile_query_service.get_all.return_value = all_profiles

    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.side_effect = lambda uid, **kw: _make_domain_user(uid)

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    result = use_case.list_all_profiles(requester_id, limit=10)

    assert len(result) == 2
    returned_ids = {dto.user_id for dto in result}
    assert requester_id not in returned_ids
    assert other_id1 in returned_ids
    assert other_id2 in returned_ids


def test_list_all_profiles_respects_public_and_not_deleted():
    requester_id = uuid4()
    private_id = uuid4()
    deleted_id = uuid4()
    public_id = uuid4()

    all_profiles = [
        PrimaryProfile(user_id=private_id, account_type="private", is_deleted=False),
        PrimaryProfile(user_id=deleted_id, account_type="public", is_deleted=True),
        PrimaryProfile(user_id=public_id, account_type="public", is_deleted=False),
    ]

    mock_profile_query_service = Mock()
    mock_profile_query_service.get_all.return_value = all_profiles

    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.side_effect = lambda uid, **kw: _make_domain_user(uid)

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    result = use_case.list_all_profiles(requester_id, limit=10)

    assert len(result) == 1
    assert result[0].user_id == public_id


def test_list_all_profiles_applies_pagination():
    requester_id = uuid4()
    ids = [uuid4() for _ in range(5)]
    all_profiles = [
        PrimaryProfile(user_id=uid, account_type="public", is_deleted=False)
        for uid in ids
    ]

    mock_profile_query_service = Mock()
    mock_profile_query_service.get_all.return_value = all_profiles

    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.side_effect = lambda uid, **kw: _make_domain_user(uid)

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    # First page
    result_page1 = use_case.list_all_profiles(requester_id, limit=2, offset=0)
    assert len(result_page1) == 2
    assert {dto.user_id for dto in result_page1} == {ids[0], ids[1]}

    # Second page
    result_page2 = use_case.list_all_profiles(requester_id, limit=2, offset=2)
    assert len(result_page2) == 2
    assert {dto.user_id for dto in result_page2} == {ids[2], ids[3]}

    # Last page (partial)
    result_page3 = use_case.list_all_profiles(requester_id, limit=2, offset=4)
    assert len(result_page3) == 1
    assert result_page3[0].user_id == ids[4]


def test_list_all_profiles_skips_missing_users():
    requester_id = uuid4()
    missing_user_id = uuid4()

    all_profiles = [
        PrimaryProfile(user_id=missing_user_id, account_type="public", is_deleted=False),
    ]

    mock_profile_query_service = Mock()
    mock_profile_query_service.get_all.return_value = all_profiles

    mock_user_query_service = Mock()
    mock_user_query_service.get_by_id.side_effect = UserNotFoundError()

    use_case = ProfileUseCase(
        user_query_service=mock_user_query_service,
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    result = use_case.list_all_profiles(requester_id, limit=10)

    assert len(result) == 0  # skipped missing user


def test_list_all_profiles_error_raises_domain_error():
    requester_id = uuid4()
    mock_profile_query_service = Mock()
    mock_profile_query_service.get_all.side_effect = RuntimeError("DB timeout")

    use_case = ProfileUseCase(
        user_query_service=Mock(),
        profile_query_service=mock_profile_query_service,
        profile_command_service=Mock(),
        outbox_repo=Mock(),
    )

    with pytest.raises(ProfileDomainError, match="Failed to list all profiles"):
        use_case.list_all_profiles(requester_id)