from __future__ import annotations
from typing import Sequence
from uuid import UUID
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from src.domain.profile.models import PrimaryProfile
from src.domain.profile.repository import PrimaryProfileRepository
from src.domain.profile.exceptions import (
    ProfileNotFoundError,
    ProfileAlreadyExistsError,
    InvalidDeltaError,
)
from src.infrastructure.apps.profiles.models import ORMProfile
from src.infrastructure.apps.profiles.mappers import ProfileMapper


class ORMPrimaryProfileRepository(PrimaryProfileRepository):
    def create(self, profile: PrimaryProfile) -> PrimaryProfile:
        if ORMProfile.objects.filter(user_id=profile.user_id).exists():
            raise ProfileAlreadyExistsError(user_id=str(profile.user_id))
        orm_profile = ProfileMapper.to_orm(profile)
        orm_profile.save()
        return ProfileMapper.to_domain(orm_profile)

    def get_by_user_id(self, user_id: UUID) -> PrimaryProfile:
        try:
            orm_profile = ORMProfile.objects.get(user_id=user_id)
        except ObjectDoesNotExist:
            raise ProfileNotFoundError(user_id=str(user_id))
        return ProfileMapper.to_domain(orm_profile)

    def update(self, profile: PrimaryProfile) -> PrimaryProfile:
        try:
            orm_profile = ORMProfile.objects.get(user_id=profile.user_id)
        except ObjectDoesNotExist:
            raise ProfileNotFoundError(user_id=str(profile.user_id))
        updated_orm = ProfileMapper.to_orm(profile, orm_profile)
        updated_orm.save()
        return ProfileMapper.to_domain(updated_orm)

    def exists_for_user(self, user_id: UUID) -> bool:
        return ORMProfile.objects.filter(user_id=user_id).exists()

    def _validate_delta(self, delta: int) -> None:
        if delta <= 0:
            raise InvalidDeltaError("delta", delta)

    def increment_followers(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        self._validate_delta(delta)
        with transaction.atomic():
            rows_updated = (
                ORMProfile.objects
                .select_for_update()
                .filter(user_id=user_id)
                .update(followers_count=F("followers_count") + delta, updated_at=timezone.now())
            )
            if rows_updated == 0:
                raise ProfileNotFoundError(user_id=str(user_id))
            return self.get_by_user_id(user_id)

    def decrement_followers(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        self._validate_delta(delta)
        with transaction.atomic():
            try:
                orm_profile = ORMProfile.objects.select_for_update().get(user_id=user_id)
            except ObjectDoesNotExist:
                raise ProfileNotFoundError(user_id=str(user_id))
            orm_profile.followers_count = max(0, orm_profile.followers_count - delta)
            orm_profile.updated_at = timezone.now()
            orm_profile.save(update_fields=["followers_count", "updated_at"])
            return ProfileMapper.to_domain(orm_profile)

    def increment_following(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        self._validate_delta(delta)
        with transaction.atomic():
            rows_updated = (
                ORMProfile.objects
                .select_for_update()
                .filter(user_id=user_id)
                .update(following_count=F("following_count") + delta, updated_at=timezone.now())
            )
            if rows_updated == 0:
                raise ProfileNotFoundError(user_id=str(user_id))
            return self.get_by_user_id(user_id)

    def decrement_following(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        self._validate_delta(delta)
        with transaction.atomic():
            try:
                orm_profile = ORMProfile.objects.select_for_update().get(user_id=user_id)
            except ObjectDoesNotExist:
                raise ProfileNotFoundError(user_id=str(user_id))
            orm_profile.following_count = max(0, orm_profile.following_count - delta)
            orm_profile.updated_at = timezone.now()
            orm_profile.save(update_fields=["following_count", "updated_at"])
            return ProfileMapper.to_domain(orm_profile)

    def increment_unread_notifications(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        self._validate_delta(delta)
        with transaction.atomic():
            rows_updated = (
                ORMProfile.objects
                .select_for_update()
                .filter(user_id=user_id)
                .update(unread_notifications_count=F("unread_notifications_count") + delta, updated_at=timezone.now())
            )
            if rows_updated == 0:
                raise ProfileNotFoundError(user_id=str(user_id))
            return self.get_by_user_id(user_id)

    def decrement_unread_notifications(self, user_id: UUID, delta: int = 1) -> PrimaryProfile:
        self._validate_delta(delta)
        with transaction.atomic():
            try:
                orm_profile = ORMProfile.objects.select_for_update().get(user_id=user_id)
            except ObjectDoesNotExist:
                raise ProfileNotFoundError(user_id=str(user_id))
            orm_profile.unread_notifications_count = max(
                0, orm_profile.unread_notifications_count - delta
            )
            orm_profile.updated_at = timezone.now()
            orm_profile.save(update_fields=["unread_notifications_count", "updated_at"])
            return ProfileMapper.to_domain(orm_profile)

    def clear_unread_notifications(self, user_id: UUID) -> PrimaryProfile:
        with transaction.atomic():
            try:
                orm_profile = ORMProfile.objects.select_for_update().get(user_id=user_id)
            except ObjectDoesNotExist:
                raise ProfileNotFoundError(user_id=str(user_id))
            if orm_profile.unread_notifications_count > 0:
                orm_profile.unread_notifications_count = 0
                orm_profile.updated_at = timezone.now()
                orm_profile.save(update_fields=["unread_notifications_count", "updated_at"])
            return ProfileMapper.to_domain(orm_profile)

    def mark_online(self, user_id: UUID) -> PrimaryProfile:
        try:
            orm_profile = ORMProfile.objects.get(user_id=user_id)
        except ObjectDoesNotExist:
            raise ProfileNotFoundError(user_id=str(user_id))
        orm_profile.last_seen_at = timezone.now()
        orm_profile.save(update_fields=["last_seen_at"])
        return ProfileMapper.to_domain(orm_profile)

    def toggle_deleted(self, user_id: UUID) -> PrimaryProfile:
        with transaction.atomic():
            try:
                orm_profile = ORMProfile.objects.select_for_update().get(user_id=user_id)
            except ObjectDoesNotExist:
                raise ProfileNotFoundError(user_id=str(user_id))
            orm_profile.is_deleted = not orm_profile.is_deleted
            orm_profile.updated_at = timezone.now()
            orm_profile.save(update_fields=["is_deleted", "updated_at"])
            return ProfileMapper.to_domain(orm_profile)

    def delete_permanently(self, user_id: UUID) -> None:
        deleted_count, _ = ORMProfile.objects.filter(user_id=user_id).delete()
        if deleted_count == 0:
            raise ProfileNotFoundError(user_id=str(user_id))

    def list_top_profiles(
        self,
        by: str = "followers",
        limit: int = 20,
        offset: int = 0
    ) -> Sequence[PrimaryProfile]:
        field_map = {
            "followers": "-followers_count",
            "following": "-following_count",
        }
        if by not in field_map:
            allowed = list(field_map.keys())
            raise ValueError(f"Invalid sort field: {by}. Must be one of {allowed}")
        orm_profiles = (
            ORMProfile.objects
            .filter(is_deleted=False)
            .order_by(field_map[by])[offset : offset + limit]
        )
        return [ProfileMapper.to_domain(p) for p in orm_profiles]
    
    def get_all(self) -> Sequence[PrimaryProfile]:
        orm_profiles = ORMProfile.objects.filter(is_deleted=False).order_by("user_id")
        return [ProfileMapper.to_domain(p) for p in orm_profiles]