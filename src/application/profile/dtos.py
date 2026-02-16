from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime, date

from src.application.user.dtos import ProfileUserDTO
from src.domain.profile.models import PrimaryProfile


class MyUserProfileDTO:
    def __init__(
        self,
        user: ProfileUserDTO,
        followers_count: int = 0,
        following_count: int = 0,
        unread_notifications_count: int = 0,
        last_seen_at: Optional[datetime] = None,
        is_deleted: bool = False,
        bio: Optional[str] = None,
        profession: Optional[str] = None,
        account_type: str = "public",
        date_of_birth: Optional[date] = None,
        gender: Optional[str] = None,
        phone: Optional[str] = None,
        location: Optional[str] = None,
        language: Optional[str] = None,
        theme: Optional[str] = None,
        cover_image: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.user_id = user.user_id
        self.user = user
        self.followers_count = followers_count
        self.following_count = following_count
        self.unread_notifications_count = unread_notifications_count
        self.last_seen_at = last_seen_at
        self.is_deleted = is_deleted
        self.bio = bio
        self.profession = profession
        self.account_type = account_type
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.phone = phone
        self.location = location
        self.language = language
        self.theme = theme
        self.cover_image = cover_image
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": str(self.user_id),
            "user": self.user.to_dict(),
            "followers_count": self.followers_count,
            "following_count": self.following_count,
            "unread_notifications_count": self.unread_notifications_count,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "is_deleted": self.is_deleted,
            "bio": self.bio,
            "profession": self.profession,
            "account_type": self.account_type,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender,
            "phone": self.phone,
            "location": self.location,
            "language": self.language,
            "theme": self.theme,
            "cover_image": self.cover_image,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_domain(cls, domain_profile: PrimaryProfile, user_dto: ProfileUserDTO) -> "MyUserProfileDTO":
        return cls(
            user=user_dto,
            followers_count=domain_profile.followers_count,
            following_count=domain_profile.following_count,
            unread_notifications_count=domain_profile.unread_notifications_count,
            last_seen_at=domain_profile.last_seen_at,
            is_deleted=domain_profile.is_deleted,
            bio=domain_profile.bio,
            profession=domain_profile.profession,
            account_type=domain_profile.account_type,
            date_of_birth=domain_profile.date_of_birth,
            gender=domain_profile.gender,
            phone=domain_profile.phone,
            location=domain_profile.location,
            language=domain_profile.language,
            theme=domain_profile.theme,
            cover_image=domain_profile.cover_image,
            created_at=domain_profile.created_at,
            updated_at=domain_profile.updated_at,
        )


class ForeignUserProfileDTO:
    def __init__(
        self,
        user: ProfileUserDTO,
        followers_count: int = 0,
        following_count: int = 0,
        bio: Optional[str] = None,
        profession: Optional[str] = None,
        account_type: str = "public",
        location: Optional[str] = None,
        cover_image: Optional[str] = None,
        created_at: Optional[datetime] = None,
        # Note: deliberately excludes private fields like phone, dob, gender, theme, unread_notifications, etc.
    ):
        self.user_id = user.user_id
        self.user = user
        self.followers_count = followers_count
        self.following_count = following_count
        self.bio = bio
        self.profession = profession
        self.account_type = account_type
        self.location = location
        self.cover_image = cover_image
        self.created_at = created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": str(self.user_id),
            "user": self.user.to_dict(),
            "followers_count": self.followers_count,
            "following_count": self.following_count,
            "bio": self.bio,
            "profession": self.profession,
            "account_type": self.account_type,
            "location": self.location,
            "cover_image": self.cover_image,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_domain(cls, domain_profile: PrimaryProfile, user_dto: ProfileUserDTO) -> "ForeignUserProfileDTO":
        return cls(
            user=user_dto,
            followers_count=domain_profile.followers_count,
            following_count=domain_profile.following_count,
            bio=domain_profile.bio,
            profession=domain_profile.profession,
            account_type=domain_profile.account_type,
            location=domain_profile.location,
            cover_image=domain_profile.cover_image,
            created_at=domain_profile.created_at,
        )