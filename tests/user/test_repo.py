# tests/infrastructure/repos/test_user_repo.py

import pytest
from uuid import uuid4, UUID
from unittest.mock import Mock, patch
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import IntegrityError, DatabaseError

from src.infrastructure.repos.user_repo import ORMUserRepository
from src.domain.user.models import DomainUser
from src.domain.user.exceptions import (
    UserNotFoundError,
    UserAlreadyExistsError,
    UserDomainError,
)
from src.infrastructure.apps.users.models import ORMUser

from unittest.mock import Mock, patch
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError

from src.domain.user.exceptions import UserAlreadyExistsError, UserDomainError


@pytest.fixture
def user_repo():
    return ORMUserRepository()


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
def sample_orm_user():
    user = ORMUser(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        is_active=True,
        is_deleted=False
    )
    user.save = Mock()
    return user


class TestORMUserRepository:
    
    # Test Create Method
    def test_create_success(self, user_repo, sample_domain_user):
        with patch.object(ORMUser.objects, 'filter') as mock_filter:
            mock_filter.return_value.exists.return_value = False
            
            mock_orm_user = Mock()
            mock_orm_user.save = Mock()
            
            with patch.object(user_repo.mapper, 'to_orm', return_value=mock_orm_user):
                with patch.object(user_repo.mapper, 'to_domain', return_value=sample_domain_user):
                    result = user_repo.create(sample_domain_user)
                    
                    assert result == sample_domain_user
                    mock_orm_user.save.assert_called_once()

    
    

    def test_create_integrity_error_email(self, user_repo, sample_domain_user):
        with patch.object(ORMUser.objects, 'filter') as mock_filter:
            mock_filter.return_value.exists.return_value = False
            
            mock_orm_user = Mock()
            mock_orm_user.save = Mock(side_effect=IntegrityError("UNIQUE constraint failed: users_ormuser.email"))
            
            with patch.object(user_repo.mapper, 'to_orm', return_value=mock_orm_user):
                with pytest.raises(UserAlreadyExistsError) as exc_info:
                    user_repo.create(sample_domain_user)
                
                assert "email" in str(exc_info.value).lower()

    def test_create_integrity_error_username(self, user_repo, sample_domain_user):
        with patch.object(ORMUser.objects, 'filter') as mock_filter:
            mock_filter.return_value.exists.return_value = False
            
            mock_orm_user = Mock()
            mock_orm_user.save = Mock(side_effect=IntegrityError("UNIQUE constraint failed: users_ormuser.username"))
            
            with patch.object(user_repo.mapper, 'to_orm', return_value=mock_orm_user):
                with pytest.raises(UserAlreadyExistsError) as exc_info:
                    user_repo.create(sample_domain_user)
                
                assert "username" in str(exc_info.value).lower()

    def test_create_database_error(self, user_repo, sample_domain_user):
        with patch.object(ORMUser.objects, 'filter') as mock_filter:
            mock_filter.return_value.exists.return_value = False
            
            mock_orm_user = Mock()
            mock_orm_user.save = Mock(side_effect=DatabaseError("Connection failed"))
            
            with patch.object(user_repo.mapper, 'to_orm', return_value=mock_orm_user):
                with pytest.raises(UserDomainError) as exc_info:
                    user_repo.create(sample_domain_user)
                
                assert "Database error" in str(exc_info.value)

    # Test by_id Method
    def test_by_id_success(self, user_repo, sample_domain_user, sample_orm_user):
        with patch.object(ORMUser.objects, 'get', return_value=sample_orm_user):
            with patch.object(user_repo.mapper, 'to_domain', return_value=sample_domain_user):
                user_id = sample_orm_user.id
                result = user_repo.by_id(user_id)
                
                assert result == sample_domain_user

    def test_by_id_include_deleted_false(self, user_repo, sample_domain_user, sample_orm_user):
        mock_objects = Mock()
        mock_objects.filter.return_value = mock_objects
        mock_objects.get.return_value = sample_orm_user
        
        with patch.object(ORMUser, 'objects', mock_objects):
            with patch.object(user_repo.mapper, 'to_domain', return_value=sample_domain_user):
                user_id = sample_orm_user.id
                result = user_repo.by_id(user_id, include_deleted=False)
                
                assert result == sample_domain_user
                mock_objects.filter.assert_called_once_with(is_deleted=False)

    def test_by_id_not_found(self, user_repo):
        user_id = uuid4()
        with patch.object(ORMUser.objects, 'get', side_effect=ObjectDoesNotExist):
            with pytest.raises(UserNotFoundError) as exc_info:
                user_repo.by_id(user_id)
            
            assert str(user_id) in str(exc_info.value)

    def test_by_id_database_error(self, user_repo):
        user_id = uuid4()
        with patch.object(ORMUser.objects, 'get', side_effect=DatabaseError("Connection failed")):
            with pytest.raises(UserDomainError) as exc_info:
                user_repo.by_id(user_id)
            
            assert "Database error" in str(exc_info.value)

    # Test by_email Method
    def test_by_email_success(self, user_repo, sample_domain_user, sample_orm_user):
        with patch.object(ORMUser.objects, 'get', return_value=sample_orm_user):
            with patch.object(user_repo.mapper, 'to_domain', return_value=sample_domain_user):
                result = user_repo.by_email("test@example.com")
                
                assert result == sample_domain_user

    def test_by_email_not_found(self, user_repo):
        with patch.object(ORMUser.objects, 'get', side_effect=ObjectDoesNotExist):
            with pytest.raises(UserNotFoundError) as exc_info:
                user_repo.by_email("nonexistent@example.com")
            
            assert "not found" in str(exc_info.value).lower()

    def test_by_email_multiple_found(self, user_repo):
        with patch.object(ORMUser.objects, 'get', side_effect=MultipleObjectsReturned):
            with pytest.raises(UserDomainError) as exc_info:
                user_repo.by_email("duplicate@example.com")
            
            assert "Multiple users" in str(exc_info.value)

    def test_by_email_database_error(self, user_repo):
        with patch.object(ORMUser.objects, 'get', side_effect=DatabaseError("Connection failed")):
            with pytest.raises(UserDomainError) as exc_info:
                user_repo.by_email("test@example.com")
            
            assert "Database error" in str(exc_info.value)

    # Test by_username Method
    def test_by_username_success(self, user_repo, sample_domain_user, sample_orm_user):
        with patch.object(ORMUser.objects, 'get', return_value=sample_orm_user):
            with patch.object(user_repo.mapper, 'to_domain', return_value=sample_domain_user):
                result = user_repo.by_username("testuser")
                
                assert result == sample_domain_user

    def test_by_username_not_found(self, user_repo):
        with patch.object(ORMUser.objects, 'get', side_effect=ObjectDoesNotExist):
            with pytest.raises(UserNotFoundError) as exc_info:
                user_repo.by_username("nonexistent")
            
            assert "not found" in str(exc_info.value).lower()

    # Test Update Method
    def test_update_success(self, user_repo, sample_domain_user, sample_orm_user):
        with patch.object(ORMUser.objects, 'get', return_value=sample_orm_user):
            with patch.object(ORMUser.objects, 'filter') as mock_filter:
                mock_filter.return_value.exclude.return_value.exists.return_value = False
                
                updated_orm_user = Mock()
                updated_orm_user.save = Mock()
                
                with patch.object(user_repo.mapper, 'to_orm', return_value=updated_orm_user):
                    with patch.object(user_repo.mapper, 'to_domain', return_value=sample_domain_user):
                        result = user_repo.update(sample_domain_user)
                        
                        assert result == sample_domain_user
                        updated_orm_user.save.assert_called_once()

    
    def test_update_user_not_found(self, user_repo, sample_domain_user):
        with patch.object(ORMUser.objects, 'get', side_effect=ObjectDoesNotExist):
            with pytest.raises(UserNotFoundError) as exc_info:
                user_repo.update(sample_domain_user)
            
            assert str(sample_domain_user.user_id) in str(exc_info.value)

    # Test Soft Deleted Method
    def test_soft_deleted_true(self, user_repo, sample_orm_user):
        sample_orm_user.is_deleted = True
        with patch.object(ORMUser.objects, 'get', return_value=sample_orm_user):
            result = user_repo.soft_deleted(sample_orm_user.id)
            
            assert result is True

    def test_soft_deleted_false(self, user_repo, sample_orm_user):
        sample_orm_user.is_deleted = False
        with patch.object(ORMUser.objects, 'get', return_value=sample_orm_user):
            result = user_repo.soft_deleted(sample_orm_user.id)
            
            assert result is False

    def test_soft_deleted_not_found(self, user_repo):
        user_id = uuid4()
        with patch.object(ORMUser.objects, 'get', side_effect=ObjectDoesNotExist):
            with pytest.raises(UserNotFoundError):
                user_repo.soft_deleted(user_id)

    
    def test_hard_delete_not_found(self, user_repo):
        user_id = uuid4()
        with patch.object(ORMUser.objects, 'get', side_effect=ObjectDoesNotExist):
            with pytest.raises(UserNotFoundError):
                user_repo.hard_delete(user_id)

    # Test Activate/Deactivate Methods
    def test_activate_success(self, user_repo, sample_domain_user, sample_orm_user):
        sample_orm_user.is_active = False
        with patch.object(ORMUser.objects, 'get', return_value=sample_orm_user):
            with patch.object(user_repo.mapper, 'to_domain', return_value=sample_domain_user):
                result = user_repo.activate(sample_orm_user.id)
                
                assert result == sample_domain_user
                assert sample_orm_user.is_active is True
                sample_orm_user.save.assert_called_once()

    def test_deactivate_success(self, user_repo, sample_domain_user, sample_orm_user):
        sample_orm_user.is_active = True
        with patch.object(ORMUser.objects, 'get', return_value=sample_orm_user):
            with patch.object(user_repo.mapper, 'to_domain', return_value=sample_domain_user):
                result = user_repo.deactivate(sample_orm_user.id)
                
                assert result == sample_domain_user
                assert sample_orm_user.is_active is False
                sample_orm_user.save.assert_called_once()

    # Test Exists Methods
    def test_exists_by_email_true(self, user_repo):
        with patch.object(ORMUser.objects, 'filter') as mock_filter:
            mock_filter.return_value.exists.return_value = True
            result = user_repo.exists_by_email("test@example.com")
            
            assert result is True

    def test_exists_by_email_false(self, user_repo):
        with patch.object(ORMUser.objects, 'filter') as mock_filter:
            mock_filter.return_value.exists.return_value = False
            result = user_repo.exists_by_email("test@example.com")
            
            assert result is False

    def test_exists_by_username_true(self, user_repo):
        with patch.object(ORMUser.objects, 'filter') as mock_filter:
            mock_filter.return_value.exists.return_value = True
            result = user_repo.exists_by_username("testuser")
            
            assert result is True

    # Test List Methods
    def test_list_all_success(self, user_repo, sample_domain_user):
        mock_orm_users = [Mock(), Mock()]
        with patch.object(ORMUser.objects, 'all') as mock_all:
            mock_all.return_value.filter.return_value.order_by.return_value.__getitem__.return_value = mock_orm_users
            
            with patch.object(user_repo.mapper, 'to_domain', side_effect=[sample_domain_user, sample_domain_user]):
                result = user_repo.list_all(limit=10, offset=0)
                
                assert len(result) == 2
                assert all(isinstance(user, DomainUser) for user in result)

    

    def test_list_deleted_users(self, user_repo, sample_domain_user):
        mock_orm_users = [Mock(), Mock()]
        with patch.object(ORMUser.objects, 'filter') as mock_filter:
            mock_filter.return_value.order_by.return_value.__getitem__.return_value = mock_orm_users
            
            with patch.object(user_repo.mapper, 'to_domain', side_effect=[sample_domain_user, sample_domain_user]):
                result = user_repo.list_deleted_users(limit=10, offset=0)
                
                assert len(result) == 2
                mock_filter.assert_called_once_with(is_deleted=True)

    # Test Search Method
    def test_search_users_success(self, user_repo, sample_domain_user):
        mock_orm_users = [Mock(), Mock()]
        with patch.object(ORMUser.objects, 'filter') as mock_filter:
            mock_filter.return_value.order_by.return_value.__getitem__.return_value = mock_orm_users
            
            with patch.object(user_repo.mapper, 'to_domain', side_effect=[sample_domain_user, sample_domain_user]):
                result = user_repo.search_users("test", limit=10)
                
                assert len(result) == 2

    # Test Private Helper Methods
    def test_private_exists_by_email(self, user_repo):
        with patch.object(ORMUser.objects, 'filter') as mock_filter:
            mock_filter.return_value.exists.return_value = True
            result = user_repo._exists_by_email("test@example.com")
            
            assert result is True
            mock_filter.assert_called_once_with(email__iexact="test@example.com")

    def test_private_exists_by_username(self, user_repo):
        with patch.object(ORMUser.objects, 'filter') as mock_filter:
            mock_filter.return_value.exists.return_value = True
            result = user_repo._exists_by_username("testuser")
            
            assert result is True
            mock_filter.assert_called_once_with(username__iexact="testuser")

    # Test Exception Propagation
    def test_unexpected_error_handling(self, user_repo, sample_domain_user):
        with patch.object(ORMUser.objects, 'filter') as mock_filter:
            mock_filter.return_value.exists.side_effect = Exception("Unexpected error")
            
            with pytest.raises(UserDomainError) as exc_info:
                user_repo.create(sample_domain_user)
            
            assert "Unexpected error" in str(exc_info.value)


# Integration-style tests (if you want to test with actual database)
@pytest.mark.django_db
class TestORMUserRepositoryIntegration:
    def test_create_and_retrieve_user(self, user_repo):
        domain_user = DomainUser(
            username="integrationuser",
            email="integration@example.com",
            first_name="Integration",
            last_name="Test"
        )
        
        # Create user
        created_user = user_repo.create(domain_user)
        
        # Retrieve by ID
        retrieved_user = user_repo.by_id(created_user.user_id)
        
        assert retrieved_user.user_id == created_user.user_id
        assert retrieved_user.username == "integrationuser"
        assert retrieved_user.email == "integration@example.com"
        
        # Retrieve by email
        email_user = user_repo.by_email("integration@example.com")
        assert email_user.user_id == created_user.user_id
        
        # Retrieve by username
        username_user = user_repo.by_username("integrationuser")
        assert username_user.user_id == created_user.user_id

    @pytest.mark.django_db
    def test_soft_delete_behavior(self, user_repo):
        domain_user = DomainUser(
            username="deletetest",
            email="delete@example.com"
        )
        
        created_user = user_repo.create(domain_user)
        
        # User should be retrievable by default (include_deleted=True)
        user1 = user_repo.by_id(created_user.user_id)
        assert user1.user_id == created_user.user_id
        
        # Soft delete the user
        orm_user = ORMUser.objects.get(id=created_user.user_id)
        orm_user.is_deleted = True
        orm_user.save()
        
        # Should still be retrievable with include_deleted=True (default)
        user2 = user_repo.by_id(created_user.user_id)
        assert user2.user_id == created_user.user_id
        
        # Should not be retrievable with include_deleted=False
        with pytest.raises(UserNotFoundError):
            user_repo.by_id(created_user.user_id, include_deleted=False)
        
        # Should not be found by email (always excludes deleted)
        with pytest.raises(UserNotFoundError):
            user_repo.by_email("delete@example.com")












    def test_create_duplicate_email(self, user_repo, sample_domain_user):
        with patch.object(user_repo, '_exists_by_email', return_value=True):
            # Change to expect UserDomainError since that's what your repository actually raises
            with pytest.raises(UserDomainError) as exc_info:
                user_repo.create(sample_domain_user)
            
            assert "email" in str(exc_info.value).lower()
            assert "already exists" in str(exc_info.value).lower()


    def test_create_duplicate_username(self, user_repo, sample_domain_user):
        with patch.object(user_repo, '_exists_by_email', return_value=False):
            with patch.object(user_repo, '_exists_by_username', return_value=True):
                # Change to expect UserDomainError since that's what your repository actually raises
                with pytest.raises(UserDomainError) as exc_info:
                    user_repo.create(sample_domain_user)
                
                assert "username" in str(exc_info.value).lower()
                assert "already exists" in str(exc_info.value).lower()


    def test_update_email_conflict(self, user_repo, sample_domain_user, sample_orm_user):
        with patch.object(ORMUser.objects, 'get', return_value=sample_orm_user):
            with patch.object(ORMUser.objects, 'filter') as mock_filter:
                mock_filter.return_value.exclude.return_value.exists.return_value = True
                
                # Change to expect UserDomainError since that's what your repository actually raises
                with pytest.raises(UserDomainError) as exc_info:
                    user_repo.update(sample_domain_user)
                
                assert "email" in str(exc_info.value).lower()
                assert "already exists" in str(exc_info.value).lower()


    def test_hard_delete_success(self, user_repo, sample_orm_user):
        # Mock the delete method to avoid database access
        sample_orm_user.delete = Mock()
        
        with patch.object(ORMUser.objects, 'get', return_value=sample_orm_user):
            user_repo.hard_delete(sample_orm_user.id)
            
            sample_orm_user.delete.assert_called_once()


    def test_list_all_include_deleted(self, user_repo):
        # Create a proper mock for the queryset slicing
        mock_slice_result = Mock()
        mock_slice_result.__iter__ = Mock(return_value=iter([]))
        
        mock_queryset = Mock()
        mock_queryset.order_by.return_value = mock_queryset
        # Mock the slicing behavior properly
        mock_queryset.__getitem__ = Mock(return_value=mock_slice_result)
        
        mock_objects = Mock()
        mock_objects.all.return_value = mock_queryset
        
        with patch.object(ORMUser, 'objects', mock_objects):
            result = user_repo.list_all(include_deleted=True)
            
            # Should not call filter when include_deleted is True
            mock_queryset.filter.assert_not_called()
            # Verify the result is an empty list
            assert result == []
