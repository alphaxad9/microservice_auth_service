# src/infrastructure/apps/profiles/models.py

from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from typing import Any
phone_validator = RegexValidator(
    regex=r"^\+[1-9]\d{6,14}$",
    message="Phone number must be in valid E.164 format (e.g., +14155552671)."
)

class ORMProfile(models.Model):
    # ⬇️ user_id IS the primary key
    user_id = models.UUIDField(primary_key=True, editable=False)

    # === Primary social metrics ===
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    unread_notifications_count = models.PositiveIntegerField(default=0)

    last_seen_at = models.DateTimeField(default=timezone.now)
    is_deleted = models.BooleanField(default=False)

    # === Extended fields ===
    profession = models.CharField(max_length=50, blank=True, null=True)

    ACCOUNT_TYPE_CHOICES = [("public", "Public"), ("private", "Private")]
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES, default="public")

    date_of_birth = models.DateField(blank=True, null=True)

    GENDER_CHOICES = [("male", "Male"), ("female", "Female"), ("other", "Other")]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)

    phone = models.CharField(
        max_length=16,
        blank=True,
        null=True,
        validators=[phone_validator],
        help_text="E.164 format (e.g., +14155552671)"
    )

    location = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z]{2}$",
                message="Location must be a valid 2-letter uppercase country code (e.g., US)."
            )
        ]
    )

    LANGUAGE_CHOICES = [("en", "English"), ("es", "Spanish"), ("fr", "French")]
    language = models.CharField(max_length=10, null=True, blank=True)


    theme = models.CharField(max_length=50, default="system")
    avatar = models.URLField(null=True, blank=True, default=None)
    bio = models.TextField(null=True, blank=True, default="")

    cover_image = models.URLField(blank=True, null=True)

    # === Timestamps ===
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "profiles"
        verbose_name = "Primary Profile"
        verbose_name_plural = "Primary Profiles"
        indexes = [
            models.Index(fields=["-followers_count"], name="profile_followers_idx"),
            models.Index(fields=["is_deleted"], name="profile_is_deleted_idx"),
            models.Index(fields=["account_type"], name="profile_account_type_idx"),
            models.Index(fields=["location"], name="profile_location_idx"),
        ]

    def __str__(self) -> str:
        return f"Profile for user {self.user_id}"

    def save(self, *args: Any, **kwargs: Any):
        # Do NOT auto-update updated_at — domain controls it
        super().save(*args, **kwargs)