from uuid import uuid4, UUID
from datetime import datetime
from typing import Optional

class DomainUser:
    def __init__(
        self,
        username: str,
        email: str,
        is_active: bool = True,
        is_deleted: bool = False,
        user_id: UUID | None = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        profile_picture: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        if not username or not email:
            raise ValueError("Username and email required")
        self.user_id = user_id or uuid4()
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.profile_picture = profile_picture
        self.is_active = is_active
        self.is_deleted = is_deleted
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def toggle_active(self) -> None:
        """Toggles the is_active status."""
        self.is_active = not self.is_active
        self.updated_at = datetime.now()

    def toggle_deleted(self) -> None:
        """Toggles the is_deleted status."""
        self.is_deleted = not self.is_deleted
        self.updated_at = datetime.now()

    def update_profile(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        profile_picture: Optional[str] = None
    ) -> None:
        """Update user profile information."""
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if profile_picture is not None:
            self.profile_picture = profile_picture
        self.updated_at = datetime.now()

    def get_full_name(self) -> str:
        """Return the full name of the user."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username