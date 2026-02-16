# tests/profile/test_profile_repo.py

import pytest
from uuid import uuid4
from django.utils import timezone

from src.domain.profile.models import PrimaryProfile
from src.domain.profile.exceptions import (
    ProfileNotFoundError,
    ProfileAlreadyExistsError,
    InvalidDeltaError,
)
from src.infrastructure.repos.profile_repo import ORMPrimaryProfileRepository
from src.infrastructure.apps.profiles.models import ORMProfile
from django.utils import timezone


# 🔑 Enable database access for all tests in this file
pytestmark = pytest.mark.django_db


@pytest.fixture
def repo():
    return ORMPrimaryProfileRepository()


@pytest.fixture
def sample_user_id():
    return uuid4()


@pytest.fixture
def base_profile_data(sample_user_id):
    return {
        "user_id": sample_user_id,
        "followers_count": 5,
        "following_count": 3,
        "unread_notifications_count": 2,
        "bio": "Hello!",
        "account_type": "public",
        "language": "en",
        "theme": "dark",
    }


@pytest.fixture
def create_profile_in_db(base_profile_data):
    orm_profile = ORMProfile.objects.create(**base_profile_data)
    return orm_profile.user_id

METHOD_TO_FIELD = {
    "increment_followers": "followers_count",
    "decrement_followers": "followers_count",
    "increment_following": "following_count",
    "decrement_following": "following_count",
    "increment_unread_notifications": "unread_notifications_count",
    "decrement_unread_notifications": "unread_notifications_count",
}

# --- CREATE ---

def test_create_profile_already_exists(repo, create_profile_in_db):
    user_id = create_profile_in_db
    profile = PrimaryProfile(user_id=user_id)
    with pytest.raises(ProfileAlreadyExistsError):
        repo.create(profile)


# --- GET ---

def test_get_by_user_id_success(repo, create_profile_in_db):
    user_id = create_profile_in_db
    profile = repo.get_by_user_id(user_id)
    assert profile.user_id == user_id
    assert profile.followers_count == 5


def test_get_by_user_id_not_found(repo):
    with pytest.raises(ProfileNotFoundError):
        repo.get_by_user_id(uuid4())


# --- EXISTS ---

def test_exists_for_user_true(repo, create_profile_in_db):
    assert repo.exists_for_user(create_profile_in_db) is True


def test_exists_for_user_false(repo):
    assert repo.exists_for_user(uuid4()) is False


# --- UPDATE ---

def test_update_profile_success(repo, create_profile_in_db):
    user_id = create_profile_in_db
    profile = repo.get_by_user_id(user_id)
    profile.bio = "Updated bio"
    profile.followers_count = 100

    updated = repo.update(profile)
    assert updated.bio == "Updated bio"
    assert updated.followers_count == 100

    # Verify in DB
    db_profile = ORMProfile.objects.get(user_id=user_id)
    assert db_profile.bio == "Updated bio"
    assert db_profile.followers_count == 100


def test_update_profile_not_found(repo):
    profile = PrimaryProfile(user_id=uuid4(), bio="test")
    with pytest.raises(ProfileNotFoundError):
        repo.update(profile)


# --- INCREMENT / DECREMENT ---

@pytest.mark.parametrize("method", ["increment_followers", "increment_following", "increment_unread_notifications"])
def test_increment_success(repo, create_profile_in_db, method):
    user_id = create_profile_in_db
    field_name = METHOD_TO_FIELD[method]
    initial = getattr(repo.get_by_user_id(user_id), field_name)

    result = getattr(repo, method)(user_id, delta=3)
    expected = initial + 3
    assert getattr(result, field_name) == expected



@pytest.mark.parametrize("method", ["decrement_followers", "decrement_following", "decrement_unread_notifications"])
def test_decrement_to_zero(repo, create_profile_in_db, method):
    user_id = create_profile_in_db
    field_name = METHOD_TO_FIELD[method]
    profile = repo.get_by_user_id(user_id)
    setattr(profile, field_name, 2)
    repo.update(profile)

    result = getattr(repo, method)(user_id, delta=5)
    assert getattr(result, field_name) == 0



@pytest.mark.parametrize("method", ["increment_followers", "decrement_followers"])
def test_delta_zero_or_negative_raises(repo, create_profile_in_db, method):
    user_id = create_profile_in_db
    with pytest.raises(InvalidDeltaError):
        getattr(repo, method)(user_id, delta=0)
    with pytest.raises(InvalidDeltaError):
        getattr(repo, method)(user_id, delta=-1)


def test_increment_nonexistent_user_raises(repo):
    with pytest.raises(ProfileNotFoundError):
        repo.increment_followers(uuid4(), delta=1)


# --- CLEAR UNREAD NOTIFICATIONS ---

def test_clear_unread_notifications_when_positive(repo, create_profile_in_db):
    user_id = create_profile_in_db
    profile = repo.get_by_user_id(user_id)
    assert profile.unread_notifications_count == 2

    result = repo.clear_unread_notifications(user_id)
    assert result.unread_notifications_count == 0


def test_clear_unread_notifications_when_zero(repo, create_profile_in_db):
    user_id = create_profile_in_db
    # Set to 0
    profile = repo.get_by_user_id(user_id)
    profile.unread_notifications_count = 0
    repo.update(profile)

    result = repo.clear_unread_notifications(user_id)
    assert result.unread_notifications_count == 0


# --- MARK ONLINE ---

def test_mark_online_updates_last_seen_not_updated_at(repo, create_profile_in_db):
    user_id = create_profile_in_db
    original = repo.get_by_user_id(user_id)
    original_updated_at = original.updated_at
    original_last_seen = original.last_seen_at

    result = repo.mark_online(user_id)

    # last_seen_at should change
    assert result.last_seen_at > original_last_seen
    # updated_at should NOT change
    assert result.updated_at == original_updated_at


def test_mark_online_nonexistent_user_raises(repo):
    with pytest.raises(ProfileNotFoundError):
        repo.mark_online(uuid4())


# --- TOGGLE DELETED ---

def test_toggle_deleted_flips_flag_and_updates_timestamp(repo, create_profile_in_db):
    user_id = create_profile_in_db
    original = repo.get_by_user_id(user_id)
    assert original.is_deleted is False
    original_updated_at = original.updated_at

    result1 = repo.toggle_deleted(user_id)
    assert result1.is_deleted is True
    assert result1.updated_at > original_updated_at

    result2 = repo.toggle_deleted(user_id)
    assert result2.is_deleted is False
    assert result2.updated_at > result1.updated_at


# --- DELETE PERMANENTLY ---

def test_delete_permanently(repo, create_profile_in_db):
    user_id = create_profile_in_db
    assert repo.exists_for_user(user_id) is True

    repo.delete_permanently(user_id)
    assert repo.exists_for_user(user_id) is False


def test_delete_permanently_nonexistent_raises(repo):
    with pytest.raises(ProfileNotFoundError):
        repo.delete_permanently(uuid4())


# --- LIST TOP PROFILES ---

def test_list_top_profiles_by_followers(repo):
    # Create 3 users with varying followers
    u1 = uuid4()
    u2 = uuid4()
    u3 = uuid4()

    ORMProfile.objects.create(user_id=u1, followers_count=100, is_deleted=False)
    ORMProfile.objects.create(user_id=u2, followers_count=200, is_deleted=False)
    ORMProfile.objects.create(user_id=u3, followers_count=50, is_deleted=False)

    top = repo.list_top_profiles(by="followers", limit=2)
    assert len(top) == 2
    assert top[0].followers_count == 200
    assert top[1].followers_count == 100


def test_list_top_profiles_excludes_deleted(repo):
    u1 = uuid4()
    u2 = uuid4()

    ORMProfile.objects.create(user_id=u1, followers_count=300, is_deleted=False)
    ORMProfile.objects.create(user_id=u2, followers_count=400, is_deleted=True)

    top = repo.list_top_profiles(by="followers", limit=5)
    assert len(top) == 1
    assert top[0].user_id == u1


def test_list_top_profiles_invalid_sort_field(repo):
    with pytest.raises(ValueError, match="Invalid sort field"):
        repo.list_top_profiles(by="invalid")


# --- TIMEZONE AWARENESS (sanity check) ---
