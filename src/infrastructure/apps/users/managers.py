from django.contrib.auth.models import BaseUserManager
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .models import ORMUser  # Forward reference to avoid circular import


class CustomUserManager(BaseUserManager["ORMUser"]):  # Use forward type reference
    def create_user(self, email: str, username: str, password: Optional[str] = None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        if not username:
            raise ValueError("The Username field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, username: str, password: Optional[str] = None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if not username:
            raise ValueError('Superuser must have a username.')

        return self.create_user(email, username, password, **extra_fields)