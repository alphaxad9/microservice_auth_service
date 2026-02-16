# src/domain/user/events.py

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


# --------------------
# User Event Type Enum
# --------------------
class UserEventType(Enum):
    """Enumeration of all possible user domain event types."""
    USER_CREATED = "user.created"
    USER_ACTIVATED = "user.activated"
    USER_DEACTIVATED = "user.deactivated"
    USER_LOGGED_IN = "user.logged_in"
    USER_LOGGED_OUT = "user.logged_out"
    USER_UPDATED = "user.updated"
    SOFT_DELETED = "user.soft_deleted"



# --------------------
# Base User Event
# --------------------
@dataclass(frozen=True, kw_only=True)
class UserEvent:
    """Base class for all user domain events."""
    user_id: UUID
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: int = 1

    def __post_init__(self):
        if not isinstance(self.user_id, UUID):
            raise TypeError("user_id must be a UUID")

    @property
    def event_type(self) -> UserEventType:
        raise NotImplementedError("Subclasses must define event_type")

    def payload(self) -> dict[str, Any]:
        return {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type.value,
            "schema_version": self.schema_version,
            "occurred_at": self.occurred_at.isoformat(),
            "user_id": str(self.user_id),
            "payload": self.payload(),
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


# --------------------
# Specific User Events
# --------------------

@dataclass(frozen=True, kw_only=True)
class UserCreated(UserEvent):
    """Emitted when a new user is created."""
    username: str
    email: str

    @property
    def event_type(self) -> UserEventType:
        return UserEventType.USER_CREATED

    def payload(self) -> dict[str, Any]:
        return {
            "username": self.username,
            "email": self.email,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserCreated":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["username"] = payload.get("username", "")
        base["email"] = payload.get("email", "")
        return cls(**base)

    # Use inherited to_dict() → keeps payload nested


@dataclass(frozen=True, kw_only=True)
class UserActivated(UserEvent):
    """Emitted when a user is activated (e.g., email confirmed)."""

    @property
    def event_type(self) -> UserEventType:
        return UserEventType.USER_ACTIVATED

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserActivated":
        base = cls.base_from_dict(data)
        return cls(**base)

    # No custom to_dict() needed


@dataclass(frozen=True, kw_only=True)
class UserDeactivated(UserEvent):
    """Emitted when a user is deactivated (e.g., admin disables account)."""

    @property
    def event_type(self) -> UserEventType:
        return UserEventType.USER_DEACTIVATED

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserDeactivated":
        base = cls.base_from_dict(data)
        return cls(**base)


@dataclass(frozen=True, kw_only=True)
class UserLoggedIn(UserEvent):
    """Emitted when a user logs in."""
    ip_address: str | None = None
    user_agent: str | None = None

    @property
    def event_type(self) -> UserEventType:
        return UserEventType.USER_LOGGED_IN

    def payload(self) -> dict[str, Any]:
        return {
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserLoggedIn":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["ip_address"] = payload.get("ip_address")
        base["user_agent"] = payload.get("user_agent")
        return cls(**base)

    # Use inherited to_dict() → payload stays nested


@dataclass(frozen=True, kw_only=True)
class UserLoggedOut(UserEvent):
    """Emitted when a user logs out."""
    ip_address: str | None = None
    user_agent: str | None = None

    @property
    def event_type(self) -> UserEventType:
        return UserEventType.USER_LOGGED_OUT

    def payload(self) -> dict[str, Any]:
        return {
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserLoggedOut":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["ip_address"] = payload.get("ip_address")
        base["user_agent"] = payload.get("user_agent")
        return cls(**base)


@dataclass(frozen=True, kw_only=True)
class UserUpdated(UserEvent):
    """Emitted when a user's profile is updated."""
    updated_fields: dict[str, Any]

    @property
    def event_type(self) -> UserEventType:
        return UserEventType.USER_UPDATED

    def payload(self) -> dict[str, Any]:
        return {
            "updated_fields": self.updated_fields,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserUpdated":
        base = cls.base_from_dict(data)
        payload = data.get("payload", {})
        base["updated_fields"] = payload.get("updated_fields", {})
        return cls(**base)
    



@dataclass(frozen=True, kw_only=True)
class UserSoftDeleted(UserEvent):
    """Emitted when a user is permanently deleted."""

    @property
    def event_type(self) -> UserEventType:
        return UserEventType.SOFT_DELETED

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserSoftDeleted":
        base = cls.base_from_dict(data)
        return cls(**base)

