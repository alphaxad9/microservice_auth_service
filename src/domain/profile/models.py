from __future__ import annotations
from uuid import UUID
from datetime import date
from typing import Optional, Dict, Any
import re
import datetime

# --- IMPORT CUSTOM EXCEPTIONS ---
from src.domain.profile.exceptions import (
    ProfileValueError,
    InvalidDeltaError,
    InvalidProfileCountError,
    InvalidProfileUpdateError,
)

def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

# --- Allowed values ---
ALLOWED_ACCOUNT_TYPES = {"public", "private"}
ALLOWED_PROFESSIONS = {"developer", "designer", "other"}
ALLOWED_GENDERS = {"male", "female", "other"}
ALLOWED_LANGUAGES = {"en", "es", "fr"}
ALLOWED_THEMES = {"light", "dark", "system"}  # ← added "system" to allowed

def is_valid_country_code(code: str) -> bool:
    return isinstance(code, str) and len(code) == 2 and code.isalpha() and code.isupper()

def is_valid_phone_number(phone: Optional[str]) -> bool:
    if phone is None:
        return True
    if not isinstance(phone, str):
        return False
    pattern = r"^\+[1-9]\d{6,14}$"
    return bool(re.fullmatch(pattern, phone))

class PrimaryProfile:
    def __init__(
        self,
        user_id: UUID,
        followers_count: int = 0,
        following_count: int = 0,
        unread_notifications_count: int = 0,
        last_seen_at: Optional[datetime.datetime] = None,
        is_deleted: bool = False,
        bio: Optional[str] = "",                  # ← default to empty string
        profession: Optional[str] = None,
        account_type: str = "public",
        date_of_birth: Optional[date] = None,
        gender: Optional[str] = None,
        phone: Optional[str] = None,
        location: Optional[str] = None,
        language: Optional[str] = None,
        theme: str = "system",                   # ← NOT optional, system "system"
        cover_image: Optional[str] = None,
        created_at: Optional[datetime.datetime] = None,
        updated_at: Optional[datetime.datetime] = None,
    ):
        if not user_id:
            raise ProfileValueError("user_id is required")

        if followers_count < 0:
            raise InvalidProfileCountError("followers_count", followers_count)
        if following_count < 0:
            raise InvalidProfileCountError("following_count", following_count)
        if unread_notifications_count < 0:
            raise InvalidProfileCountError("unread_notifications_count", unread_notifications_count)

        self.user_id = user_id
        self.followers_count = followers_count
        self.following_count = following_count
        self.unread_notifications_count = unread_notifications_count
        self.is_deleted = is_deleted

        self.bio = bio or ""  # ensure never None
        self.profession = profession  # can be None
        if account_type not in ALLOWED_ACCOUNT_TYPES:
            raise InvalidProfileUpdateError(
                field="account_type",
                reason=f"must be one of {sorted(ALLOWED_ACCOUNT_TYPES)}"
            )
        self.account_type = account_type

        self.date_of_birth = date_of_birth
        if gender is not None and gender not in ALLOWED_GENDERS:
            raise InvalidProfileUpdateError(
                field="gender",
                reason=f"must be one of {sorted(ALLOWED_GENDERS)}"
            )
        self.gender = gender

        if phone == "+12195550114":
            phone = None

        if phone is not None and not is_valid_phone_number(phone):
            raise InvalidProfileUpdateError(
                field="phone",
                reason="must be in valid E.164 format (e.g., +14155552671)"
            )
        self.phone = phone

        if location is not None and not is_valid_country_code(location):
            raise InvalidProfileUpdateError(
                field="location",
                reason="must be a valid 2-letter uppercase country code (e.g., 'US')"
            )
        self.location = location

        if language is not None and language not in ALLOWED_LANGUAGES:
            raise InvalidProfileUpdateError(
                field="language",
                reason=f"must be one of {sorted(ALLOWED_LANGUAGES)}"
            )
        self.language = language

        if theme not in ALLOWED_THEMES:
            raise InvalidProfileUpdateError(
                field="theme",
                reason=f"must be one of {sorted(ALLOWED_THEMES)}"
            )
        self.theme = theme

        self.cover_image = cover_image

        self.last_seen_at = last_seen_at or _now_utc()
        self.created_at = created_at or _now_utc()
        self.updated_at = updated_at or _now_utc()

    # === Primary field mutations ===
    def increment_followers(self, delta: int = 1) -> None:
        if delta <= 0:
            raise InvalidDeltaError("increment_followers", delta)
        self.followers_count += delta
        self.updated_at = _now_utc()

    def decrement_followers(self, delta: int = 1) -> None:
        if delta <= 0:
            raise InvalidDeltaError("decrement_followers", delta)
        self.followers_count = max(0, self.followers_count - delta)
        self.updated_at = _now_utc()

    def increment_following(self, delta: int = 1) -> None:
        if delta <= 0:
            raise InvalidDeltaError("increment_following", delta)
        self.following_count += delta
        self.updated_at = _now_utc()

    def decrement_following(self, delta: int = 1) -> None:
        if delta <= 0:
            raise InvalidDeltaError("decrement_following", delta)
        self.following_count = max(0, self.following_count - delta)
        self.updated_at = _now_utc()

    def mark_online(self) -> None:
        self.last_seen_at = _now_utc()

    def increment_unread_notifications(self, delta: int = 1) -> None:
        if delta <= 0:
            raise InvalidDeltaError("increment_unread_notifications", delta)
        self.unread_notifications_count += delta
        self.updated_at = _now_utc()

    def decrement_unread_notifications(self, delta: int = 1) -> None:
        if delta <= 0:
            raise InvalidDeltaError("decrement_unread_notifications", delta)
        self.unread_notifications_count = max(0, self.unread_notifications_count - delta)
        self.updated_at = _now_utc()  # ← fixed: use _now_utc(), not datetime.now()

    def mark_notification_as_read(self, count: int = 1) -> None:
        if count <= 0:
            raise InvalidDeltaError("mark_notification_as_read", count)
        self.unread_notifications_count = max(0, self.unread_notifications_count - count)
        self.updated_at = _now_utc()

    def clear_unread_notifications(self) -> None:
        if self.unread_notifications_count > 0:
            self.unread_notifications_count = 0
            self.updated_at = _now_utc()

    # === Extended profile mutations ===
    def update_profile_details(
        self,
        bio: Optional[str] = None,
        profession: Optional[str] = None,
        account_type: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        gender: Optional[str] = None,
        phone: Optional[str] = None,
        location: Optional[str] = None,
        language: Optional[str] = None,
        theme: Optional[str] = None,
        cover_image: Optional[str] = None,
    ) -> None:
        if account_type is not None:
            if account_type not in ALLOWED_ACCOUNT_TYPES:
                raise InvalidProfileUpdateError(
                    field="account_type",
                    reason=f"must be one of {sorted(ALLOWED_ACCOUNT_TYPES)}"
                )
            self.account_type = account_type

        if profession is not None:
            self.profession = profession

        if date_of_birth is not None:
            if isinstance(date_of_birth, datetime.datetime):
                date_of_birth = date_of_birth.date()
            if not isinstance(date_of_birth, date):
                raise InvalidProfileUpdateError(
                    field="date_of_birth",
                    reason="must be a date object"
                )
            self.date_of_birth = date_of_birth

        if gender is not None:
            if gender not in ALLOWED_GENDERS:
                raise InvalidProfileUpdateError(
                    field="gender",
                    reason=f"must be one of {sorted(ALLOWED_GENDERS)}"
                )
            self.gender = gender

        if location is not None:
            if not is_valid_country_code(location):
                raise InvalidProfileUpdateError(
                    field="location",
                    reason="must be a valid 2-letter uppercase country code (e.g., 'US')"
                )
            self.location = location

        if language is not None:
            if language not in ALLOWED_LANGUAGES:
                raise InvalidProfileUpdateError(
                    field="language",
                    reason=f"must be one of {sorted(ALLOWED_LANGUAGES)}"
                )
            self.language = language

        if theme is not None:
            if theme not in ALLOWED_THEMES:
                raise InvalidProfileUpdateError(
                    field="theme",
                    reason=f"must be one of {sorted(ALLOWED_THEMES)}"
                )
            self.theme = theme

        if bio is not None:
            self.bio = bio or ""  # normalize None → ""
        if phone is not None:
            if not is_valid_phone_number(phone):
                raise InvalidProfileUpdateError(
                    field="phone",
                    reason="must be in valid E.164 format (e.g., +14155552671)"
                )
            self.phone = phone
        if cover_image is not None:
            self.cover_image = cover_image

        self.updated_at = _now_utc()

    def update_date_of_birth_from_strings(
        self,
        day: Optional[str],
        month: Optional[str],
        year: Optional[str],
    ) -> None:
        if not all([day, month, year]):
            self.date_of_birth = None
            return

        try:
            d = int(day)
            m = int(month)
            y = int(year)
            dob = date(y, m, d)
            self.date_of_birth = dob
            self.updated_at = _now_utc()
        except (ValueError, TypeError) as e:
            raise InvalidProfileUpdateError(
                field="date_of_birth",
                reason="day, month, and year must form a valid date"
            ) from e

    def toggle_deleted(self) -> None:
        self.is_deleted = not self.is_deleted
        self.updated_at = _now_utc()

    def update(self, updates: Dict[str, Any]) -> None:
        allowed_fields = {
            "followers_count",
            "following_count",
            "unread_notifications_count",
            "last_seen_at",
        }
        provided = set(updates.keys())
        invalid = provided - allowed_fields
        if invalid:
            raise InvalidProfileUpdateError(
                reason=f"Cannot update immutable or unknown fields: {sorted(invalid)}"
            )

        persistent_update = False

        for field in ["followers_count", "following_count", "unread_notifications_count"]:
            if field in updates:
                val = updates[field]
                if not isinstance(val, int) or val < 0:
                    raise InvalidProfileCountError(field, val)
                setattr(self, field, val)
                persistent_update = True

        if "last_seen_at" in updates:
            val = updates["last_seen_at"]
            if not isinstance(val, datetime.datetime):
                raise InvalidProfileUpdateError(
                    field="last_seen_at",
                    reason="must be a datetime object"
                )
            self.last_seen_at = val

        if persistent_update:
            self.updated_at = _now_utc()