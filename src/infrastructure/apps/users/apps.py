# src/infrastructure/apps/users/apps.py

from django.apps import AppConfig
import logging
logger = logging.getLogger(__name__)

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.infrastructure.apps.users'
    def ready(self):
        try:
            # Wire dependencies
            from src.messaging.user.config import configure_user_event_bus
            from src.messaging.user.event_bus import userbus
            from src.infrastructure.repos.user_repo import ORMUserRepository
            from src.application.user.services import UserQueryServiceImpl

            from src.application.profile.usecases import ProfileUseCase
            from src.application.profile.services import PrimaryProfileQueryServiceImpl, PrimaryProfileCommandServiceImpl
            from src.infrastructure.repos.profile_repo import ORMPrimaryProfileRepository  
            profile_repository = ORMPrimaryProfileRepository()
            from src.infrastructure.repos.outbox.orm_repository import DjangoOutBoxORMRepository

            
            user_repo = ORMUserRepository()
            user_query_service = UserQueryServiceImpl(user_repo)
            profile_query_service = PrimaryProfileQueryServiceImpl(profile_repository)

            profile_command_service = PrimaryProfileCommandServiceImpl(profile_repository, profile_query_service)
            outbox_repo = DjangoOutBoxORMRepository()

            primary_profile_use_case = ProfileUseCase(
                profile_query_service=profile_query_service,
                profile_command_service=profile_command_service,
                user_query_service=user_query_service,
                outbox_repo=outbox_repo,
            )

            configure_user_event_bus(
                event_bus=userbus,
                user_query_service=user_query_service,
                primary_profile_use_case=primary_profile_use_case
            )
        except Exception as e:
            logging.error(f"Error wiring dependencies: {e}")