from __future__ import annotations
from src.domain.profile.models import PrimaryProfile
from src.infrastructure.apps.profiles.models import ORMProfile


class ProfileMapper:
    @staticmethod
    def to_domain(orm_profile: ORMProfile) -> PrimaryProfile:
        return PrimaryProfile(
            user_id=orm_profile.user_id,
            followers_count=orm_profile.followers_count,
            following_count=orm_profile.following_count,
            unread_notifications_count=orm_profile.unread_notifications_count,
            last_seen_at=orm_profile.last_seen_at,
            is_deleted=orm_profile.is_deleted,
            bio=orm_profile.bio or "",  # ensure not None
            profession=orm_profile.profession,
            account_type=orm_profile.account_type,
            date_of_birth=orm_profile.date_of_birth,
            gender=orm_profile.gender,
            phone=orm_profile.phone,
            location=orm_profile.location,
            language=orm_profile.language,
            theme=orm_profile.theme or "system",  # fallback
            cover_image=orm_profile.cover_image,
            created_at=orm_profile.created_at,
            updated_at=orm_profile.updated_at,
        )

    @staticmethod
    def to_orm(
        domain_profile: PrimaryProfile,
        orm_profile: ORMProfile | None = None,
    ) -> ORMProfile:
        if orm_profile is None:
            orm_profile = ORMProfile(user_id=domain_profile.user_id)

        # Assign fields — ensure no None where ORM forbids it
        orm_profile.followers_count = domain_profile.followers_count
        orm_profile.following_count = domain_profile.following_count
        orm_profile.unread_notifications_count = domain_profile.unread_notifications_count
        orm_profile.last_seen_at = domain_profile.last_seen_at
        orm_profile.is_deleted = domain_profile.is_deleted
        orm_profile.bio = domain_profile.bio or ""  # ← critical: never None
        orm_profile.profession = domain_profile.profession
        orm_profile.account_type = domain_profile.account_type
        orm_profile.date_of_birth = domain_profile.date_of_birth
        orm_profile.gender = domain_profile.gender
        orm_profile.phone = domain_profile.phone
        orm_profile.location = domain_profile.location
        orm_profile.language = domain_profile.language
        orm_profile.theme = domain_profile.theme or "system"  # ← critical: never None
        orm_profile.cover_image = domain_profile.cover_image
        orm_profile.created_at = domain_profile.created_at
        orm_profile.updated_at = domain_profile.updated_at

        return orm_profile