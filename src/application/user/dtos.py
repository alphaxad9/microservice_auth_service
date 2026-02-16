# File: src/application/user/dtos.py
from __future__ import annotations
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from src.domain.user.models import DomainUser

class UserDTO:
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": str(self.user_id),
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "profile_picture": self.profile_picture,
            "is_active": self.is_active,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserDTO":
        # Handle datetime conversion
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")
        
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            user_id=UUID(data["user_id"]) if data.get("user_id") else None,
            username=data["username"],
            email=data["email"],
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            profile_picture=data.get("profile_picture"),
            is_active=data.get("is_active", True),
            is_deleted=data.get("is_deleted", False),
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def from_domain(cls, domain_user: DomainUser) -> "UserDTO":
        
        return cls(
            user_id=domain_user.user_id,      
            username=domain_user.username,     
            email=domain_user.email,           
            first_name=domain_user.first_name, 
            last_name=domain_user.last_name,   
            profile_picture=domain_user.profile_picture, 
            is_active=domain_user.is_active,   
            is_deleted=domain_user.is_deleted, 
            created_at=domain_user.created_at, 
            updated_at=domain_user.updated_at, 
        )
    






class ProfileUserDTO:
    def __init__(
        self,
        username: str,
        is_active: bool = True,
        user_id: UUID | None = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        profile_picture: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        self.user_id = user_id or uuid4()
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.profile_picture = profile_picture
        self.is_active = is_active
        self.created_at = created_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": str(self.user_id),
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "profile_picture": self.profile_picture,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProfileUserDTO":
        # Handle datetime conversion
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")
        
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            user_id=UUID(data["user_id"]) if data.get("user_id") else None,
            username=data["username"],
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            profile_picture=data.get("profile_picture"),
            is_active=data.get("is_active", True),
            created_at=created_at,
        )

    @classmethod
    def from_domain(cls, domain_user: DomainUser) -> "ProfileUserDTO":
        
        return cls(
            user_id=domain_user.user_id,      
            username=domain_user.username,     
            first_name=domain_user.first_name, 
            last_name=domain_user.last_name,   
            profile_picture=domain_user.profile_picture, 
            is_active=domain_user.is_active,   
            created_at=domain_user.created_at, 
        )