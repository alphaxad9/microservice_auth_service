# src/application/profile/factories.py
from typing import Optional

from src.application.profile.usecases import ProfileUseCase
from src.application.profile.services import (
    PrimaryProfileQueryServiceImpl,
    PrimaryProfileCommandServiceImpl,
)
from src.infrastructure.repos.profile_repo import ORMPrimaryProfileRepository
from src.infrastructure.repos.user_repo import ORMUserRepository
from src.infrastructure.repos.outbox.orm_repository import DjangoOutBoxORMRepository
from src.application.user.interfaces import UserQueryService
from src.application.user.services import UserQueryServiceImpl


def create_profile_use_case(
    profile_repo: Optional[ORMPrimaryProfileRepository] = None,
    user_repo: Optional[ORMUserRepository] = None,
    outbox_repo: Optional[DjangoOutBoxORMRepository] = None,
) -> ProfileUseCase:
    """
    Factory function to create and wire the ProfileUseCase with its dependencies.
    Allows injection of mock or alternative implementations for testing or different environments.
    """
    # Use defaults if not provided
    if profile_repo is None:
        profile_repo = ORMPrimaryProfileRepository()
    if user_repo is None:
        user_repo = ORMUserRepository()
    if outbox_repo is None:
        outbox_repo = DjangoOutBoxORMRepository()

    # Create query and command services
    profile_query_service = PrimaryProfileQueryServiceImpl(profile_repo)
    profile_command_service = PrimaryProfileCommandServiceImpl(
        profile_repository=profile_repo,
        profile_query_service=profile_query_service,
    )

    # User query service (needed by ProfileUseCase)
    user_query_service: UserQueryService = UserQueryServiceImpl(user_repo)

    # Assemble use case
    use_case = ProfileUseCase(
        user_query_service=user_query_service,
        profile_query_service=profile_query_service,
        profile_command_service=profile_command_service,
        outbox_repo=outbox_repo,
    )
    return use_case


_profile_use_case_instance: Optional[ProfileUseCase] = None


def get_profile_use_case() -> ProfileUseCase:
    """
    Returns a singleton instance of ProfileUseCase.
    Prefer `create_profile_use_case()` for per-request or test-safe instantiation.
    """
    global _profile_use_case_instance
    if _profile_use_case_instance is None:
        _profile_use_case_instance = create_profile_use_case()
    return _profile_use_case_instance


def create_profile_query_service(
    profile_repo: Optional[ORMPrimaryProfileRepository] = None,
) -> PrimaryProfileQueryServiceImpl:
    """
    Factory function to create PrimaryProfileQueryServiceImpl.
    """
    if profile_repo is None:
        profile_repo = ORMPrimaryProfileRepository()
    return PrimaryProfileQueryServiceImpl(profile_repo)


def create_profile_command_service(
    profile_repo: Optional[ORMPrimaryProfileRepository] = None,
    profile_query_service: Optional[PrimaryProfileQueryServiceImpl] = None,
) -> PrimaryProfileCommandServiceImpl:
    """
    Factory function to create PrimaryProfileCommandServiceImpl.
    """
    if profile_repo is None:
        profile_repo = ORMPrimaryProfileRepository()
    if profile_query_service is None:
        profile_query_service = create_profile_query_service(profile_repo)

    return PrimaryProfileCommandServiceImpl(
        profile_repository=profile_repo,
        profile_query_service=profile_query_service,
    )