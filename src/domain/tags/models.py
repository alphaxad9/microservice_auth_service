from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

@dataclass(frozen=True)
class DomainTag:
    id: UUID
    name: str
    usage_count: int = field(default=0)
    created_at: Optional[datetime] = field(default=None)

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise TypeError("id must be a UUID instance")
        if not isinstance(self.name, str):
            raise ValueError("name must be a string")
        if not isinstance(self.usage_count, int) or self.usage_count < 0:
            raise ValueError("usage_count must be a non-negative integer")
        
        normalized = self.name.strip().lower()
        if not normalized:
            raise ValueError("name must be a non-empty string after stripping whitespace")
        
        if self.name != normalized:
            object.__setattr__(self, 'name', normalized)

        if self.created_at is not None and self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")

    def increment_usage(self, by: int = 1) -> "DomainTag":
        """Return a new DomainTag with usage_count increased by `by`."""
        if by <= 0:
            raise ValueError("Increment amount must be positive")
        return DomainTag(
            id=self.id,
            name=self.name,
            usage_count=self.usage_count + by,
            created_at=self.created_at
        )

    def decrement_usage(self, by: int = 1) -> "DomainTag":
        """Return a new DomainTag with usage_count decreased by `by` (never below 0)."""
        if by <= 0:
            raise ValueError("Decrement amount must be positive")
        new_count = max(0, self.usage_count - by)
        return DomainTag(
            id=self.id,
            name=self.name,
            usage_count=new_count,
            created_at=self.created_at
        )