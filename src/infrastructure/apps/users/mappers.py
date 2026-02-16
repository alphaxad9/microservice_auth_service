from typing import Optional
from src.infrastructure.apps.users.models import ORMUser
from src.domain.user.models import DomainUser

class UserMapper:
    """Maps between DomainUser and ORMUser."""

    @staticmethod
    def to_domain(orm_user: ORMUser) -> DomainUser:
        """Convert an ORMUser instance into a DomainUser entity."""

        return DomainUser(
            user_id=orm_user.id,
            username=orm_user.username,
            email=orm_user.email,
            first_name=orm_user.first_name,
            last_name=orm_user.last_name,
            profile_picture=(
                orm_user.profile_picture.url 
                if orm_user.profile_picture 
                else None
            ),
            is_active=orm_user.is_active,
            is_deleted=orm_user.is_deleted,
            created_at=orm_user.created_at,
            updated_at=orm_user.updated_at,
        )

    @staticmethod
    def to_orm(domain_user: DomainUser, orm_instance: Optional[ORMUser] = None) -> ORMUser:
        """
        Convert a DomainUser into an ORMUser instance.
        
        If `orm_instance` is provided, update it.
        Otherwise create a new ORMUser.
        """

        orm_user = orm_instance or ORMUser()

        orm_user.id = domain_user.user_id
        orm_user.username = domain_user.username
        orm_user.email = domain_user.email
        orm_user.first_name = domain_user.first_name
        orm_user.last_name = domain_user.last_name
        
        # Profile picture: domain stores string path, ORM stores FileField
        if domain_user.profile_picture:
            orm_user.profile_picture = domain_user.profile_picture

        orm_user.is_active = domain_user.is_active
        orm_user.is_deleted = domain_user.is_deleted

        # Usually Django handles these—but Domain may override them
        orm_user.created_at = domain_user.created_at
        orm_user.updated_at = domain_user.updated_at

        return orm_user
