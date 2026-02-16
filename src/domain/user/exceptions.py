# src/domain/user/exceptions.py

from __future__ import annotations


class UserDomainError(Exception):
    """Base exception for all user-related domain errors."""
    pass


class UserValueError(UserDomainError, ValueError):
    """Raised when a user-related value is invalid (e.g., malformed email, empty username)."""
    pass


class UserNotFoundError(UserDomainError, LookupError):
    """Raised when a user is not found in the repository or database."""
    def __init__(self, user_id: str | None = None, message: str | None = None):
        if message is None:
            message = f"User not found" + (f" (ID: {user_id})" if user_id else "")
        self.user_id = user_id
        super().__init__(message)


class UserAlreadyExistsError(UserDomainError):
    """Raised when attempting to create a user that already exists (e.g., duplicate email or username)."""
    def __init__(self,  message: str | None = None):
        if message is None:
            message = f"User with already exists"
        super().__init__(message)


class InvalidEmailError(UserValueError):
    """Raised when an email address is syntactically invalid."""
    def __init__(self,  message: str | None = None):
        if message is None:
            message = f"Invalid email address"
      
        super().__init__(message)


class InvalidUsernameError(UserValueError):
    """Raised when a username fails validation (e.g., too short, invalid characters)."""
    def __init__(self, username: str,  message: str | None = None):
        if message is None:
            message = f"Invalid username: '{username}'"           
        self.username = username
        super().__init__(message)


class UserNotActiveError(UserDomainError):
    """Raised when an operation requires an active user, but the user is deactivated."""
    def __init__(self, user_id: str, message: str | None = None):
        if message is None:
            message = f"User {user_id} is not active"
        self.user_id = user_id
        super().__init__(message)


class AuthenticationError(UserDomainError):
    """Base exception for authentication failures."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials (e.g., password) are incorrect."""
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message)


class UserNotLoggedInError(AuthenticationError):
    """Raised when an operation requires an authenticated user, but none is present."""
    def __init__(self, message: str = "User is not logged in"):
        super().__init__(message)


class AccountLockedError(AuthenticationError):
    """Raised when a user account is temporarily locked (e.g., due to too many failed attempts)."""
    def __init__(self, user_id: str, message: str | None = None):
        if message is None:
            message = f"Account for user {user_id} is locked"
        self.user_id = user_id
        super().__init__(message)


class EmailNotVerifiedError(UserDomainError):
    """Raised when an operation requires a verified email, but it hasn't been confirmed."""
    def __init__(self, user_id: str, message: str | None = None):
        if message is None:
            message = f"Email for user {user_id} is not verified"
        self.user_id = user_id
        super().__init__(message)