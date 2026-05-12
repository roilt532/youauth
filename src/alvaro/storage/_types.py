from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AssetMeta:
    key: str
    bucket: str
    etag: str
    size_bytes: int
    content_type: str


@dataclass(frozen=True)
class BackgroundAsset:
    key: str
    niche_id: str
    filename: str


class StorageError(Exception):
    def __init__(self, key: str, operation: str, reason: str) -> None:
        super().__init__(f"{operation} failed key={key}: {reason}")
        self.key = key
        self.operation = operation
        self.reason = reason
