from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class ProfilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.infrastructure.apps.profiles'
    def ready(self):
        try:
            # Wire dependencies for profile event handling
            from src.messaging.profile.config import configure_profile_event_bus
            from src.infrastructure.repos.profile_repo import ORMPrimaryProfileRepository
            from src.application.profile.services import PrimaryProfileQueryServiceImpl

            profile_repo = ORMPrimaryProfileRepository()
            profile_query_service = PrimaryProfileQueryServiceImpl(profile_repo)

            configure_profile_event_bus(
                profile_query_service=profile_query_service,
            )
        except Exception as e:
            logger.error(f"Error wiring profile dependencies: {e}", exc_info=True)