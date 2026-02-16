# src/application/user/factories.py

from typing import Optional

from src.application.user.usecases import UserUseCase
from src.application.user.services import UserQueryServiceImpl, UserCommandServiceImpl
from src.infrastructure.repos.user_repo import ORMUserRepository
from src.infrastructure.repos.outbox.orm_repository import DjangoOutBoxORMRepository


def create_user_use_case(
    user_repo: Optional[ORMUserRepository] = None,
    outbox_repo: Optional[DjangoOutBoxORMRepository] = None,
) -> UserUseCase:
    """
    Factory function to create and wire the UserUseCase with its dependencies.
    Allows injection of mock or alternative implementations for testing or different environments.
    """
    # Use defaults if not provided
    if user_repo is None:
        user_repo = ORMUserRepository()
    if outbox_repo is None:
        outbox_repo = DjangoOutBoxORMRepository()

    # Create services
    user_query_service = UserQueryServiceImpl(user_repo)
    user_command_service = UserCommandServiceImpl(user_repo, user_query_service)
    
    # Use case
    use_case = UserUseCase(
        user_query_service=user_query_service,
        user_command_service=user_command_service,
        outbox_repo=outbox_repo
    )
    return use_case


_user_use_case_instance: Optional[UserUseCase] = None


def get_user_use_case() -> UserUseCase:
    """
    Returns a singleton instance of UserUseCase.
    Prefer `create_user_use_case()` for per-request or test-safe instantiation.
    """
    global _user_use_case_instance
    if _user_use_case_instance is None:
        _user_use_case_instance = create_user_use_case()
    return _user_use_case_instance


def create_user_query_service(
    user_repo: Optional[ORMUserRepository] = None
) -> UserQueryServiceImpl:
    """
    Factory function to create UserQueryServiceImpl.
    """
    if user_repo is None:
        user_repo = ORMUserRepository()
    return UserQueryServiceImpl(user_repo)


def create_user_command_service(
    user_repo: Optional[ORMUserRepository] = None,
    user_query_service: Optional[UserQueryServiceImpl] = None
) -> UserCommandServiceImpl:
    """
    Factory function to create UserCommandServiceImpl.
    """
    if user_repo is None:
        user_repo = ORMUserRepository()
    if user_query_service is None:
        user_query_service = create_user_query_service(user_repo)
    
    return UserCommandServiceImpl(user_repo, user_query_service)