from __future__ import annotations
import logging
from typing import Sequence, List
from typing import Optional
from uuid import UUID
from src.domain.user.exceptions import UserNotFoundError
from src.application.profile.dtos import MyUserProfileDTO, ForeignUserProfileDTO
from src.application.user.dtos import ProfileUserDTO
from src.application.user.interfaces import UserQueryService
from src.domain.profile.events import *
from src.domain.profile.exceptions import *
from src.domain.outbox.repositories import OutboxRepository
from src.domain.outbox.events import OutboxEvent
from src.domain.profile.models import PrimaryProfile
from src.application.profile.interfaces import PrimaryProfileQueryService, PrimaryProfileCommandService


logger = logging.getLogger(__name__)


class ProfileUseCase:
    """
    Use cases for profile management.
    Handles profile creation (idempotent) and updates with event publishing.
    """

    def __init__(
        self,
        user_query_service: UserQueryService,
        profile_query_service: PrimaryProfileQueryService,
        profile_command_service: PrimaryProfileCommandService,
        outbox_repo: OutboxRepository,
    ):
        self._user_query_service = user_query_service
        self._profile_query_service = profile_query_service
        self._profile_command_service = profile_command_service
        self._outbox_repo = outbox_repo

    def create_profile(self, user_id: UUID) -> MyUserProfileDTO:
        """
        Idempotently create a profile for a user.
        
        If a profile already exists, returns it without modification.
        Otherwise, creates a new profile, publishes ProfileCreated event,
        and returns the DTO.
        
        Args:
            user_id: ID of the user to create a profile for
            
        Returns:
            MyUserProfileDTO: The user's profile (new or existing)
            
        Raises:
            UserNotFoundError: If the user does not exist
            ProfileDomainError: On unexpected errors during creation
        """
        try:
            # Ensure user exists (required for DTO)
            domain_user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            if domain_user.is_deleted:
                raise ProfileDomainError(f"Cannot create profile for soft-deleted user: {user_id}")
            user_dto = ProfileUserDTO.from_domain(domain_user)

            # Check if profile already exists
            if self._profile_query_service.exists_for_user(user_id):
                logger.debug("Profile already exists for user %s; returning existing profile", user_id)
                existing_profile = self._profile_query_service.get_by_user_id(user_id)
                return MyUserProfileDTO.from_domain(existing_profile, user_dto)

            # Create new profile
            new_profile = PrimaryProfile(user_id=user_id)
            created_profile = self._profile_command_service.create_profile(new_profile)

            # Publish domain event
            domain_event = ProfileCreated(
                user_id=user_id,
            )
            outbox_event = OutboxEvent(
                event_type=domain_event.event_type.value,
                event_payload=domain_event.to_dict(),
                aggregate_id=user_id,
                aggregate_type="Profile",
            )
            self._outbox_repo.save(outbox_event)

            logger.info("Profile created for user: %s", user_id)
            return MyUserProfileDTO.from_domain(created_profile, user_dto)

        except ProfileAlreadyExistsError:
            # This should not occur due to the existence check, but guard against race conditions
            logger.warning("Race condition: profile already exists for user %s during creation", user_id)
            existing_profile = self._profile_query_service.get_by_user_id(user_id)
            user_dto = ProfileUserDTO.from_domain(self._user_query_service.get_by_id(user_id))
            return MyUserProfileDTO.from_domain(existing_profile, user_dto)

        except (ProfileNotFoundError, ProfileDomainError, UserNotFoundError):
            raise
        except Exception as e:
            logger.error("Unexpected error during profile creation for user %s: %s", user_id, e, exc_info=True)
            raise ProfileDomainError("Failed to create profile.") from e
    
    def update_profile(
        self,
        user_id: UUID,
        bio: Optional[str] = None,
        profession: Optional[str] = None,
        account_type: Optional[str] = None,
        date_of_birth: Optional[str] = None,  # expects ISO date string, e.g., "1990-05-15"
        gender: Optional[str] = None,
        phone: Optional[str] = None,
        location: Optional[str] = None,
        language: Optional[str] = None,
        theme: Optional[str] = None,
        cover_image: Optional[str] = None,
    ) -> MyUserProfileDTO:
        
        try:
            # Ensure profile exists
            current_profile = self._profile_query_service.get_by_user_id(user_id)
            domain_user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            user_dto = ProfileUserDTO.from_domain(domain_user)

            # Prepare update data (only non-None values)
            update_kwargs = {
                k: v for k, v in {
                    "bio": bio,
                    "profession": profession,
                    "account_type": account_type,
                    "gender": gender,
                    "phone": phone,
                    "location": location,
                    "language": language,
                    "theme": theme,
                    "cover_image": cover_image,
                }.items() if v is not None
            }

            # Handle date_of_birth separately (from string)
            if date_of_birth is not None:
                from datetime import date as DateClass
                try:
                    dob = DateClass.fromisoformat(date_of_birth)
                    update_kwargs["date_of_birth"] = dob
                except ValueError as e:
                    raise InvalidProfileUpdateError(
                        field="date_of_birth",
                        reason="must be a valid ISO date string (YYYY-MM-DD)"
                    ) from e

            if not update_kwargs:
                logger.debug("No fields provided for update; returning current profile for user %s", user_id)
                return MyUserProfileDTO.from_domain(current_profile, user_dto)

            # Apply update to domain model
            current_profile.update_profile_details(**update_kwargs)

            # Persist via command service
            updated_profile = self._profile_command_service.update_profile(current_profile)

            # Publish domain event
            domain_event = ProfileUpdated(
                user_id=user_id,
                updated_fields=update_kwargs,
            )
            outbox_event = OutboxEvent(
                event_type=domain_event.event_type.value,
                event_payload=domain_event.to_dict(),
                aggregate_id=user_id,
                aggregate_type="Profile",
            )
            self._outbox_repo.save(outbox_event)

            logger.info("Profile updated for user: %s with fields: %s", user_id, list(update_kwargs.keys()))
            return MyUserProfileDTO.from_domain(updated_profile, user_dto)

        except (ProfileNotFoundError, InvalidProfileUpdateError):
            raise
        except Exception as e:
            logger.error("Unexpected error during profile update for user %s: %s", user_id, e, exc_info=True)
            raise ProfileDomainError("Failed to update profile.") from e
        



    
    def increment_followers(self, user_id: UUID, delta: int = 1) -> MyUserProfileDTO:
        
        try:
            current_profile = self._profile_query_service.get_by_user_id(user_id)
            domain_user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            user_dto = ProfileUserDTO.from_domain(domain_user)

            # Apply domain mutation
            current_profile.increment_followers(delta)

            # Persist
            updated_profile = self._profile_command_service.increment_followers(user_id, delta)

            # Publish event
            domain_event = FollowersIncremented(
                user_id=user_id,
                delta=delta,
                new_count=updated_profile.followers_count,
            )
            outbox_event = OutboxEvent(
                event_type=domain_event.event_type.value,
                event_payload=domain_event.to_dict(),
                aggregate_id=user_id,
                aggregate_type="Profile",
            )
            self._outbox_repo.save(outbox_event)

            logger.info("Followers incremented for user %s by %d (new count: %d)", user_id, delta, updated_profile.followers_count)
            return MyUserProfileDTO.from_domain(updated_profile, user_dto)

        except (ProfileNotFoundError, InvalidDeltaError):
            raise
        except Exception as e:
            logger.error("Unexpected error incrementing followers for user %s: %s", user_id, e, exc_info=True)
            raise ProfileDomainError("Failed to increment followers.") from e

    def decrement_followers(self, user_id: UUID, delta: int = 1) -> MyUserProfileDTO:
        """
        Atomically decrement the followers count (never below zero).

        Args and exceptions mirror `increment_followers`.
        """
        try:
            current_profile = self._profile_query_service.get_by_user_id(user_id)
            domain_user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            user_dto = ProfileUserDTO.from_domain(domain_user)

            current_profile.decrement_followers(delta)
            updated_profile = self._profile_command_service.decrement_followers(user_id, delta)

            domain_event = FollowersDecremented(
                user_id=user_id,
                delta=delta,
                new_count=updated_profile.followers_count,
            )
            outbox_event = OutboxEvent(
                event_type=domain_event.event_type.value,
                event_payload=domain_event.to_dict(),
                aggregate_id=user_id,
                aggregate_type="Profile",
            )
            self._outbox_repo.save(outbox_event)

            logger.info("Followers decremented for user %s by %d (new count: %d)", user_id, delta, updated_profile.followers_count)
            return MyUserProfileDTO.from_domain(updated_profile, user_dto)

        except (ProfileNotFoundError, InvalidDeltaError):
            raise
        except Exception as e:
            logger.error("Unexpected error decrementing followers for user %s: %s", user_id, e, exc_info=True)
            raise ProfileDomainError("Failed to decrement followers.") from e

    def increment_following(self, user_id: UUID, delta: int = 1) -> MyUserProfileDTO:
        """
        Atomically increment the following count.
        """
        try:
            current_profile = self._profile_query_service.get_by_user_id(user_id)
            domain_user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            user_dto = ProfileUserDTO.from_domain(domain_user)

            current_profile.increment_following(delta)
            updated_profile = self._profile_command_service.increment_following(user_id, delta)

            domain_event = FollowingIncremented(
                user_id=user_id,
                delta=delta,
                new_count=updated_profile.following_count,
            )
            outbox_event = OutboxEvent(
                event_type=domain_event.event_type.value,
                event_payload=domain_event.to_dict(),
                aggregate_id=user_id,
                aggregate_type="Profile",
            )
            self._outbox_repo.save(outbox_event)

            logger.info("Following count incremented for user %s by %d (new count: %d)", user_id, delta, updated_profile.following_count)
            return MyUserProfileDTO.from_domain(updated_profile, user_dto)

        except (ProfileNotFoundError, InvalidDeltaError):
            raise
        except Exception as e:
            logger.error("Unexpected error incrementing following for user %s: %s", user_id, e, exc_info=True)
            raise ProfileDomainError("Failed to increment following.") from e

    def decrement_following(self, user_id: UUID, delta: int = 1) -> MyUserProfileDTO:
        """
        Atomically decrement the following count (never below zero).
        """
        try:
            current_profile = self._profile_query_service.get_by_user_id(user_id)
            domain_user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            user_dto = ProfileUserDTO.from_domain(domain_user)

            current_profile.decrement_following(delta)
            updated_profile = self._profile_command_service.decrement_following(user_id, delta)

            domain_event = FollowingDecremented(
                user_id=user_id,
                delta=delta,
                new_count=updated_profile.following_count,
            )
            outbox_event = OutboxEvent(
                event_type=domain_event.event_type.value,
                event_payload=domain_event.to_dict(),
                aggregate_id=user_id,
                aggregate_type="Profile",
            )
            self._outbox_repo.save(outbox_event)

            logger.info("Following count decremented for user %s by %d (new count: %d)", user_id, delta, updated_profile.following_count)
            return MyUserProfileDTO.from_domain(updated_profile, user_dto)

        except (ProfileNotFoundError, InvalidDeltaError):
            raise
        except Exception as e:
            logger.error("Unexpected error decrementing following for user %s: %s", user_id, e, exc_info=True)
            raise ProfileDomainError("Failed to decrement following.") from e

    def increment_unread_notifications(self, user_id: UUID, delta: int = 1) -> MyUserProfileDTO:
        """
        Atomically increment unread notifications count.
        """
        try:
            current_profile = self._profile_query_service.get_by_user_id(user_id)
            domain_user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            user_dto = ProfileUserDTO.from_domain(domain_user)

            current_profile.increment_unread_notifications(delta)
            updated_profile = self._profile_command_service.increment_unread_notifications(user_id, delta)

            domain_event = NotificationsIncremented(
                user_id=user_id,
                delta=delta,
                new_count=updated_profile.unread_notifications_count,
            )
            outbox_event = OutboxEvent(
                event_type=domain_event.event_type.value,
                event_payload=domain_event.to_dict(),
                aggregate_id=user_id,
                aggregate_type="Profile",
            )
            self._outbox_repo.save(outbox_event)

            logger.info("Unread notifications incremented for user %s by %d (new count: %d)", user_id, delta, updated_profile.unread_notifications_count)
            return MyUserProfileDTO.from_domain(updated_profile, user_dto)

        except (ProfileNotFoundError, InvalidDeltaError):
            raise
        except Exception as e:
            logger.error("Unexpected error incrementing notifications for user %s: %s", user_id, e, exc_info=True)
            raise ProfileDomainError("Failed to increment unread notifications.") from e

    def decrement_unread_notifications(self, user_id: UUID, delta: int = 1) -> MyUserProfileDTO:
        """
        Atomically decrement unread notifications count (never below zero).
        """
        try:
            current_profile = self._profile_query_service.get_by_user_id(user_id)
            domain_user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            user_dto = ProfileUserDTO.from_domain(domain_user)

            current_profile.decrement_unread_notifications(delta)
            updated_profile = self._profile_command_service.decrement_unread_notifications(user_id, delta)

            # Note: There's no "NotificationsDecremented" event in your spec — only "NotificationsIncremented" and "NotificationsCleared"
            # Since you don't have a decremented event, consider whether you want to emit one.
            # But based on your event list, it seems decrements are handled silently or via other means.
            # However, for consistency, if you decide to emit an event, you'd need to define it.
            # For now, **no event is published** on decrement (as per your current event model).

            logger.info("Unread notifications decremented for user %s by %d (new count: %d)", user_id, delta, updated_profile.unread_notifications_count)
            return MyUserProfileDTO.from_domain(updated_profile, user_dto)

        except (ProfileNotFoundError, InvalidDeltaError):
            raise
        except Exception as e:
            logger.error("Unexpected error decrementing notifications for user %s: %s", user_id, e, exc_info=True)
            raise ProfileDomainError("Failed to decrement unread notifications.") from e

    def clear_unread_notifications(self, user_id: UUID) -> MyUserProfileDTO:
        """
        Set unread notifications count to zero (only if > 0).
        """
        try:
            current_profile = self._profile_query_service.get_by_user_id(user_id)
            domain_user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            user_dto = ProfileUserDTO.from_domain(domain_user)

            previous_count = current_profile.unread_notifications_count
            current_profile.clear_unread_notifications()
            updated_profile = self._profile_command_service.clear_unread_notifications(user_id)

            if previous_count > 0:
                domain_event = NotificationsCleared(
                    user_id=user_id,
                    previous_count=previous_count,
                )
                outbox_event = OutboxEvent(
                    event_type=domain_event.event_type.value,
                    event_payload=domain_event.to_dict(),
                    aggregate_id=user_id,
                    aggregate_type="Profile",
                )
                self._outbox_repo.save(outbox_event)
                logger.info("Unread notifications cleared for user %s (was: %d)", user_id, previous_count)
            else:
                logger.debug("No unread notifications to clear for user %s", user_id)

            return MyUserProfileDTO.from_domain(updated_profile, user_dto)

        except ProfileNotFoundError:
            raise
        except Exception as e:
            logger.error("Unexpected error clearing notifications for user %s: %s", user_id, e, exc_info=True)
            raise ProfileDomainError("Failed to clear unread notifications.") from e
        

    def toggle_deleted(self, user_id: UUID) -> MyUserProfileDTO:
        """
        Toggle the soft-deleted status of a profile.
        Only the profile owner (or admin via separate flow) should call this.
        """
        try:
            current_profile = self._profile_query_service.get_by_user_id(user_id)
            domain_user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            user_dto = ProfileUserDTO.from_domain(domain_user)

            current_profile.toggle_deleted()
            updated_profile = self._profile_command_service.update_profile(current_profile)

            # Publish event
            domain_event = ProfileSoftDeletedToggled(
                user_id=user_id,
                is_deleted=updated_profile.is_deleted,
            )
            outbox_event = OutboxEvent(
                event_type=domain_event.event_type.value,
                event_payload=domain_event.to_dict(),
                aggregate_id=user_id,
                aggregate_type="Profile",
            )
            self._outbox_repo.save(outbox_event)

            logger.info("Profile soft-delete toggled for user: %s (is_deleted=%s)", user_id, updated_profile.is_deleted)
            return MyUserProfileDTO.from_domain(updated_profile, user_dto)

        except (ProfileNotFoundError, ProfileDomainError, UserNotFoundError):
            raise
        except Exception as e:
            logger.error("Unexpected error in toggle_deleted for user %s: %s", user_id, e, exc_info=True)
            raise ProfileDomainError("Failed to toggle profile deletion status.") from e

    def mark_online(self, user_id: UUID) -> MyUserProfileDTO:
        """
        Update the user's last_seen_at to current UTC time.
        Typically called on heartbeat or activity detection.
        """
        try:
            current_profile = self._profile_query_service.get_by_user_id(user_id)
            domain_user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            user_dto = ProfileUserDTO.from_domain(domain_user)

            current_profile.mark_online()
            updated_profile = self._profile_command_service.update_profile(current_profile)

            # Publish event
            domain_event = UserMarkedOnline(
                user_id=user_id,
                last_seen_at=updated_profile.last_seen_at,
            )
            outbox_event = OutboxEvent(
                event_type=domain_event.event_type.value,
                event_payload=domain_event.to_dict(),
                aggregate_id=user_id,
                aggregate_type="Profile",
            )
            self._outbox_repo.save(outbox_event)

            logger.debug("User marked online: %s", user_id)
            return MyUserProfileDTO.from_domain(updated_profile, user_dto)

        except (ProfileNotFoundError, ProfileDomainError, UserNotFoundError):
            raise
        except Exception as e:
            logger.error("Unexpected error in mark_online for user %s: %s", user_id, e, exc_info=True)
            raise ProfileDomainError("Failed to mark user as online.") from e

    def get_by_user_id(self, user_id: UUID, requester_id: UUID) -> MyUserProfileDTO | ForeignUserProfileDTO:
        """
        Retrieve a profile by user_id.
        Returns MyUserProfileDTO if requester == user_id, else ForeignUserProfileDTO.
        """
        try:
            profile = self._profile_query_service.get_by_user_id(user_id)
            domain_user = self._user_query_service.get_by_id(user_id, include_deleted=False)
            user_dto = ProfileUserDTO.from_domain(domain_user)

            if requester_id == user_id:
                return MyUserProfileDTO.from_domain(profile, user_dto)
            else:
                # Optional: enforce account_type privacy later
                return ForeignUserProfileDTO.from_domain(profile, user_dto)

        except (ProfileNotFoundError, UserNotFoundError):
            raise
        except Exception as e:
            logger.error("Unexpected error in get_by_user_id for user %s: %s", user_id, e, exc_info=True)
            raise ProfileDomainError("Failed to retrieve profile.") from e

    def exists_for_user(self, user_id: UUID) -> bool:
        """Check if a profile exists for the given user."""
        try:
            return self._profile_query_service.exists_for_user(user_id)
        except Exception as e:
            logger.error("Error checking profile existence for user %s: %s", user_id, e, exc_info=True)
            # Existence check should not fail loudly; return False on error?
            return False

    def list_top_profiles(self, requester_id: UUID, limit: int = 10) -> Sequence[ForeignUserProfileDTO]:
        """
        List top public profiles (e.g., by followers), excluding the requester's own profile.
        Only returns ForeignUserProfileDTO (no private data).
        """
        try:
            # Assume query service returns list excluding requester automatically,
            # or we filter afterward
            profiles = self._profile_query_service.list_top_profiles(limit=limit + 5)  # over-fetch to compensate for filtering

            filtered = [
                p for p in profiles
                if p.user_id != requester_id and p.account_type == "public" and not p.is_deleted
            ][:limit]

            # Fetch associated domain users in batch if needed (assume user DTO already linked or fetchable)
            result: List[ForeignUserProfileDTO] = []
            for profile in filtered:
                try:
                    domain_user = self._user_query_service.get_by_id(profile.user_id, include_deleted=False)
                    user_dto = ProfileUserDTO.from_domain(domain_user)
                    result.append(ForeignUserProfileDTO.from_domain(profile, user_dto))
                except UserNotFoundError:
                    continue  # skip if user missing

            logger.debug("Returned %d top profiles for requester %s", len(result), requester_id)
            return result

        except Exception as e:
            logger.error("Unexpected error in list_top_profiles for requester %s: %s", requester_id, e, exc_info=True)
            raise ProfileDomainError("Failed to list top profiles.") from e

    def list_all_profiles(
        self,
        requester_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> Sequence[ForeignUserProfileDTO]:
        """
        List all public, non-deleted profiles (excluding requester's own).
        Intended for admin or public directory use — apply strict access control in practice.
        
        Args:
            requester_id: ID of the user making the request.
            limit: Max number of profiles to return (default: 50).
            offset: Pagination offset (default: 0).

        Returns:
            List of ForeignUserProfileDTO (no private data).
        """
        try:
            # Fetch all profiles (non-deleted) from query service
            all_profiles = self._profile_query_service.get_all()

            # Apply filtering: public, not deleted, not requester
            filtered = [
                p for p in all_profiles
                if p.user_id != requester_id
                and p.account_type == "public"
                and not p.is_deleted
            ]

            # Apply pagination
            paginated = filtered[offset : offset + limit]

            # Map to DTOs
            result: List[ForeignUserProfileDTO] = []
            for profile in paginated:
                try:
                    domain_user = self._user_query_service.get_by_id(profile.user_id, include_deleted=False)
                    user_dto = ProfileUserDTO.from_domain(domain_user)
                    result.append(ForeignUserProfileDTO.from_domain(profile, user_dto))
                except UserNotFoundError:
                    continue  # skip orphaned profiles

            logger.debug(
                "Returned %d public profiles (offset=%d, limit=%d) for requester %s",
                len(result), offset, limit, requester_id
            )
            return result

        except Exception as e:
            logger.error(
                "Unexpected error in list_all_profiles for requester %s: %s",
                requester_id, e, exc_info=True
            )
            raise ProfileDomainError("Failed to list all profiles.") from e