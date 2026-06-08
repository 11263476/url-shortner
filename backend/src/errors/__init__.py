from src.errors.base import AppError
from src.errors.common import (
    NotFoundError, ConflictError, BadRequestError, ForbiddenError,
    UnauthorizedError, RateLimitError, InternalError,
)
from src.errors.auth import (
    EmailAlreadyExists, InvalidCredentials, TokenExpired, TokenRevoked,
    InvalidToken, OAuthNotConfigured, OAuthFailed, CSRFValidationFailed,
    UserNotFound, InvalidResetToken, InvalidVerifyToken,
)
from src.errors.url import (
    URLNotFound, AliasReserved, AliasConflict, URLDisabled, URLExpired,
    URLPasswordRequired, URLPasswordIncorrect, FolderNotInWorkspace,
    CannotGenerateShortCode,
)
from src.errors.workspace import (
    WorkspaceNotFound, OnlyAdminCanInvite, CannotInviteOwner, AlreadyMember,
    PendingInviteExists, InviteNotFound, InviteExpired, InviteEmailMismatch,
    CannotRemoveOwner, OnlyOwnerCanChangeRoles, MemberNotFound, RoleTooLow,
)

__all__ = [
    "AppError",
    "NotFoundError", "ConflictError", "BadRequestError", "ForbiddenError",
    "UnauthorizedError", "RateLimitError", "InternalError",
    "EmailAlreadyExists", "InvalidCredentials", "TokenExpired", "TokenRevoked",
    "InvalidToken", "OAuthNotConfigured", "OAuthFailed", "CSRFValidationFailed",
    "UserNotFound", "InvalidResetToken", "InvalidVerifyToken",
    "URLNotFound", "AliasReserved", "AliasConflict", "URLDisabled", "URLExpired",
    "URLPasswordRequired", "URLPasswordIncorrect", "FolderNotInWorkspace",
    "CannotGenerateShortCode",
    "WorkspaceNotFound", "OnlyAdminCanInvite", "CannotInviteOwner", "AlreadyMember",
    "PendingInviteExists", "InviteNotFound", "InviteExpired", "InviteEmailMismatch",
    "CannotRemoveOwner", "OnlyOwnerCanChangeRoles", "MemberNotFound", "RoleTooLow",
]
