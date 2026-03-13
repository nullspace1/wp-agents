"""Type definitions for Resource view and permissions."""

from typing import TypedDict


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
    permissions: dict[str, list[str]]
