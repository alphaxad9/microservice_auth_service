from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date, timezone
from enum import Enum
from typing import Dict, Any
from uuid import UUID, uuid4


# ----------------------
# Profile Event Type Enum
# ----------------------
class ProfileEventType(Enum):
    """Enumeration of all possible profile domain event types."""
    PROFILE_CREATED = "profile.created"
    PROFILE_UPDATED = "profile.updated"
    FOLLOWERS_INCREMENTED = "profile.followers_incremented"
    FOLLOWERS_DECREMENTED = "profile.followers_decremented"
    FOLLOWING_INCREMENTED = "profile.following_incremented"
    FOLLOWING_DECREMENTED = "profile.following_decremented"
    NOTIFICATIONS_INCREMENTED = "profile.notifications_incremented"
    NOTIFICATIONS_CLEARED = "profile.notifications_cleared"
    PROFILE_SOFT_DELETED_TOGGLED = "profile.soft_deleted_toggled"
    USER_MARKED_ONLINE = "profile.user_marked_online"


# ----------------------
# Base Profile Event
# ----------------------
def _safe_json(obj: Any) -> Any:
    """Convert objects to JSON-serializable versions recursively."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _safe_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_safe_json(v) for v in obj]
    return obj


@dataclass(frozen=True, kw_only=True)
class ProfileEvent:
    user_id: UUID
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: int = 1

    def __post_init__(self):
        if not isinstance(self.user_id, UUID):
            raise TypeError("user_id must be a UUID")

    @property
    def event_type(self) -> ProfileEventType:
        raise NotImplementedError

    def payload(self) -> dict[str, Any]:
        return {}

    def to_dict(self) -> dict[str, Any]:
        """Final serialized version used by OutboxEvent."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type.value,
            "schema_version": self.schema_version,
            "occurred_at": self.occurred_at.isoformat(),
            "user_id": str(self.user_id),
            "payload": _safe_json(self.payload()),
        }


    @classmethod
    def base_from_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "user_id": UUID(data["user_id"]),
            "event_id": UUID(data.get("event_id", str(uuid4()))),
            "occurred_at": (
                datetime.fromisoformat(data["occurred_at"])
                if "occurred_at" in data
                else datetime.now(timezone.utc)
            ),
            "schema_version": data.get("schema_version", 1),
        }


# ----------------------
# Specific Profile Events
# ----------------------

@dataclass(frozen=True, kw_only=True)
class ProfileCreated(ProfileEvent):
    """Emitted when a primary profile is created for a user."""
    followers_count: int = 0
    following_count: int = 0
    unread_notifications_count: int = 0

    @property
    def event_type(self) -> ProfileEventType:
        return ProfileEventType.PROFILE_CREATED

    def payload(self) -> dict[str, Any]:
        return {
            "followers_count": self.followers_count,
            "following_count": self.following_count,
            "unread_notifications_count": self.unread_notifications_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProfileCreated":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["followers_count"] = payload.get("followers_count", 0)
        base["following_count"] = payload.get("following_count", 0)
        base["unread_notifications_count"] = payload.get("unread_notifications_count", 0)
        return cls(**base)



@dataclass(frozen=True, kw_only=True)
class ProfileUpdated(ProfileEvent):
    updated_fields: dict[str, Any]

    @property
    def event_type(self) -> ProfileEventType:
        return ProfileEventType.PROFILE_UPDATED

    def payload(self) -> Dict[str, Any]:
        # Deep-safe conversion
        return {
            "updated_fields": _safe_json(self.updated_fields)
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProfileUpdated":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["updated_fields"] = payload.get("updated_fields", {})
        return cls(**base)

@dataclass(frozen=True, kw_only=True)
class FollowersIncremented(ProfileEvent):
    """Emitted when the follower count is increased."""
    delta: int
    new_count: int

    @property
    def event_type(self) -> ProfileEventType:
        return ProfileEventType.FOLLOWERS_INCREMENTED

    def payload(self) -> dict[str, Any]:
        return {
            "delta": self.delta,
            "new_count": self.new_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FollowersIncremented":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["delta"] = payload.get("delta", 0)
        base["new_count"] = payload.get("new_count", 0)
        return cls(**base)


@dataclass(frozen=True, kw_only=True)
class FollowersDecremented(ProfileEvent):
    """Emitted when the follower count is decreased."""
    delta: int
    new_count: int

    @property
    def event_type(self) -> ProfileEventType:
        return ProfileEventType.FOLLOWERS_DECREMENTED

    def payload(self) -> dict[str, Any]:
        return {
            "delta": self.delta,
            "new_count": self.new_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FollowersDecremented":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["delta"] = payload.get("delta", 0)
        base["new_count"] = payload.get("new_count", 0)
        return cls(**base)


@dataclass(frozen=True, kw_only=True)
class FollowingIncremented(ProfileEvent):
    """Emitted when the following count is increased."""
    delta: int
    new_count: int

    @property
    def event_type(self) -> ProfileEventType:
        return ProfileEventType.FOLLOWING_INCREMENTED

    def payload(self) -> dict[str, Any]:
        return {
            "delta": self.delta,
            "new_count": self.new_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FollowingIncremented":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["delta"] = payload.get("delta", 0)
        base["new_count"] = payload.get("new_count", 0)
        return cls(**base)


@dataclass(frozen=True, kw_only=True)
class FollowingDecremented(ProfileEvent):
    """Emitted when the following count is decreased."""
    delta: int
    new_count: int

    @property
    def event_type(self) -> ProfileEventType:
        return ProfileEventType.FOLLOWING_DECREMENTED

    def payload(self) -> dict[str, Any]:
        return {
            "delta": self.delta,
            "new_count": self.new_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FollowingDecremented":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["delta"] = payload.get("delta", 0)
        base["new_count"] = payload.get("new_count", 0)
        return cls(**base)


@dataclass(frozen=True, kw_only=True)
class NotificationsIncremented(ProfileEvent):
    """Emitted when unread notifications count is increased."""
    delta: int
    new_count: int

    @property
    def event_type(self) -> ProfileEventType:
        return ProfileEventType.NOTIFICATIONS_INCREMENTED

    def payload(self) -> dict[str, Any]:
        return {
            "delta": self.delta,
            "new_count": self.new_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationsIncremented":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["delta"] = payload.get("delta", 0)
        base["new_count"] = payload.get("new_count", 0)
        return cls(**base)


@dataclass(frozen=True, kw_only=True)
class NotificationsCleared(ProfileEvent):
    """Emitted when unread notifications are cleared (set to zero)."""
    previous_count: int

    @property
    def event_type(self) -> ProfileEventType:
        return ProfileEventType.NOTIFICATIONS_CLEARED

    def payload(self) -> dict[str, Any]:
        return {
            "previous_count": self.previous_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationsCleared":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["previous_count"] = payload.get("previous_count", 0)
        return cls(**base)


@dataclass(frozen=True, kw_only=True)
class ProfileSoftDeletedToggled(ProfileEvent):
    """Emitted when the profile's soft-delete status is toggled."""
    is_deleted: bool

    @property
    def event_type(self) -> ProfileEventType:
        return ProfileEventType.PROFILE_SOFT_DELETED_TOGGLED

    def payload(self) -> dict[str, Any]:
        return {
            "is_deleted": self.is_deleted,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProfileSoftDeletedToggled":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["is_deleted"] = payload.get("is_deleted", False)
        return cls(**base)


@dataclass(frozen=True, kw_only=True)
class UserMarkedOnline(ProfileEvent):
    """Emitted when a user's last_seen_at is updated (e.g., via heartbeat or activity)."""
    last_seen_at: datetime

    @property
    def event_type(self) -> ProfileEventType:
        return ProfileEventType.USER_MARKED_ONLINE

    def payload(self) -> dict[str, Any]:
        return {
            "last_seen_at": self.last_seen_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserMarkedOnline":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        last_seen_str = payload.get("last_seen_at")
        if last_seen_str:
            base["last_seen_at"] = datetime.fromisoformat(last_seen_str)
        else:
            base["last_seen_at"] = datetime.now(timezone.utc)
        return cls(**base)