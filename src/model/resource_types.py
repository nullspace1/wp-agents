"""Type definitions for Resource view and permissions."""

from typing import TypedDict


class PermissionsDict(TypedDict):
    """Permissions for user, group, and other."""
    get: bool
    post: bool
    patch: bool
    delete: bool


class ResourcePermissionsDict(TypedDict):
    """Permissions breakdown by user, group, and other."""
    user: PermissionsDict
    group: PermissionsDict
    other: PermissionsDict


class ResourceViewDict(TypedDict):
    """Resource metadata returned by view method."""
    name: str
    type: str
    author: str
    group: str
    created_at: str
    description: str
    operations: dict[str, str]
    operation_timestamps: dict[str, str | None]
    last_error: str | None
    permissions: ResourcePermissionsDict
