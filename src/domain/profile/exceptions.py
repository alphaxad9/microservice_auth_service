from __future__ import annotations


class ProfileDomainError(Exception):
    """Base exception for all profile-related domain errors."""
    pass


class ProfileValueError(ProfileDomainError, ValueError):
    """Raised when a profile-related value is invalid (e.g., negative count, malformed ID)."""
    pass


class ProfileNotFoundError(ProfileDomainError, LookupError):
    """Raised when a profile is not found in the repository or database."""
    def __init__(self, user_id: str | None = None, message: str | None = None):
        if message is None:
            message = f"Profile not found" + (f" (User ID: {user_id})" if user_id else "")
        self.user_id = user_id
        super().__init__(message)


class ProfileAlreadyExistsError(ProfileDomainError):
    """Raised when attempting to create a profile that already exists for a given user."""
    def __init__(self, user_id: str | None = None, message: str | None = None):
        if message is None:
            message = f"Profile already exists" + (f" for user {user_id}" if user_id else "")
        self.user_id = user_id
        super().__init__(message)


class InvalidProfileCountError(ProfileValueError):
    """Raised when a count value (e.g., followers, notifications) is invalid (e.g., negative)."""
    def __init__(self, field: str, value: int, message: str | None = None):
        if message is None:
            message = f"Invalid value for '{field}': {value} (must be non-negative)"
        self.field = field
        self.value = value
        super().__init__(message)


class InvalidDeltaError(ProfileValueError):
    """Raised when a delta (increment/decrement amount) is invalid (e.g., zero or negative)."""
    def __init__(self, operation: str, delta: int, message: str | None = None):
        if message is None:
            message = f"Invalid delta for '{operation}': {delta} (must be positive)"
        self.operation = operation
        self.delta = delta
        super().__init__(message)


# === Extended Profile Field Exceptions ===

class InvalidBioError(ProfileValueError):
    """Raised when the bio exceeds length limits or contains invalid content."""
    def __init__(self, bio: str | None = None, max_length: int = 500, message: str | None = None):
        if message is None:
            if bio is None:
                message = "Bio cannot be null"
            else:
                message = f"Bio exceeds maximum length of {max_length} characters (got {len(bio)})"
        self.bio = bio
        self.max_length = max_length
        super().__init__(message)


class InvalidProfessionError(ProfileValueError):
    """Raised when profession is not in the allowed list."""
    def __init__(self, profession: str, allowed: set[str], message: str | None = None):
        if message is None:
            message = f"Invalid profession '{profession}'. Must be one of: {sorted(allowed)}"
        self.profession = profession
        self.allowed = allowed
        super().__init__(message)


class InvalidAccountTypeError(ProfileValueError):
    """Raised when account_type is not 'public' or 'private'."""
    def __init__(self, account_type: str, allowed: set[str], message: str | None = None):
        if message is None:
            message = f"Invalid account type '{account_type}'. Must be one of: {sorted(allowed)}"
        self.account_type = account_type
        self.allowed = allowed
        super().__init__(message)


class InvalidDateOfBirthError(ProfileValueError):
    """Raised when date_of_birth is in the future, too old, or malformed."""
    def __init__(self, date_of_birth: str | None = None, reason: str = "invalid", message: str | None = None):
        if message is None:
            message = f"Invalid date of birth: {reason}"
            if date_of_birth:
                message += f" (value: {date_of_birth})"
        self.date_of_birth = date_of_birth
        self.reason = reason
        super().__init__(message)


class InvalidGenderError(ProfileValueError):
    """Raised when gender is not in the allowed set."""
    def __init__(self, gender: str, allowed: set[str], message: str | None = None):
        if message is None:
            message = f"Invalid gender '{gender}'. Must be one of: {sorted(allowed)}"
        self.gender = gender
        self.allowed = allowed
        super().__init__(message)


class InvalidPhoneNumberError(ProfileValueError):
    """Raised when phone number is not in valid E.164 format."""
    def __init__(self, phone: str, message: str | None = None):
        if message is None:
            message = f"Invalid phone number '{phone}'. Must be in E.164 format (e.g., +14155552671)"
        self.phone = phone
        super().__init__(message)


class InvalidLocationError(ProfileValueError):
    """Raised when location is not a valid 2-letter uppercase country code."""
    def __init__(self, location: str, message: str | None = None):
        if message is None:
            message = f"Invalid location '{location}'. Must be a valid 2-letter uppercase country code (e.g., US)"
        self.location = location
        super().__init__(message)


class InvalidLanguageError(ProfileValueError):
    """Raised when language is not in the allowed set."""
    def __init__(self, language: str, allowed: set[str], message: str | None = None):
        if message is None:
            message = f"Invalid language '{language}'. Must be one of: {sorted(allowed)}"
        self.language = language
        self.allowed = allowed
        super().__init__(message)


class InvalidThemeError(ProfileValueError):
    """Raised when theme is not in the allowed set."""
    def __init__(self, theme: str, allowed: set[str], message: str | None = None):
        if message is None:
            message = f"Invalid theme '{theme}'. Must be one of: {sorted(allowed)}"
        self.theme = theme
        self.allowed = allowed
        super().__init__(message)


class InvalidCoverImageError(ProfileValueError):
    """Raised when cover_image is not a valid URL or exceeds size/format constraints."""
    def __init__(self, cover_image: str, reason: str = "invalid URL", message: str | None = None):
        if message is None:
            message = f"Invalid cover image: {reason} (value: {cover_image})"
        self.cover_image = cover_image
        self.reason = reason
        super().__init__(message)


# === General Update & Access Exceptions ===

class ProfileUpdateError(ProfileDomainError):
    """Raised when a profile update fails due to business logic constraints."""
    pass


class ProfileConcurrencyError(ProfileDomainError):
    """Raised when concurrent profile updates cause a conflict."""
    pass


class ProfileAccessDeniedError(ProfileDomainError):
    """Raised when attempting to access a profile without required permissions (e.g., private profile)."""
    def __init__(self, target_user_id: str, viewer_user_id: str | None = None, message: str | None = None):
        if message is None:
            message = f"Access denied to profile of user {target_user_id}"
            if viewer_user_id:
                message += f" (viewer: {viewer_user_id})"
        self.target_user_id = target_user_id
        self.viewer_user_id = viewer_user_id
        super().__init__(message)


class InvalidProfileUpdateError(ProfileValueError):
    """Raised as a fallback when a profile update request contains invalid parameters."""
    def __init__(self, field: str | None = None, reason: str | None = None, message: str | None = None):
        if message is None:
            base = "Invalid profile update request"
            if field:
                base += f" for field '{field}'"
            if reason:
                base += f": {reason}"
            message = base
        self.field = field
        self.reason = reason
        super().__init__(message)