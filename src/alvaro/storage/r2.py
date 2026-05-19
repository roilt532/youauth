from __future__ import annotations

import os
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from loguru import logger

from alvaro.storage._types import AssetMeta, BackgroundAsset, StorageError


class R2Client:
    def __init__(
        self,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        bucket: str,
    ) -> None:
        self._bucket = bucket
        self._s3: Any = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
            config=Config(retries={"max_attempts": 3, "mode": "adaptive"}),
        )

    def upload_asset(self, key: str, data: bytes, content_type: str) -> AssetMeta:
        try:
            self._s3.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)
            head = self._s3.head_object(Bucket=self._bucket, Key=key)
            etag = str(head["ETag"]).strip('"')
            size = int(head["ContentLength"])
            logger.debug("r2 upload key={} bytes={}", key, size)
            return AssetMeta(
                key=key,
                bucket=self._bucket,
                etag=etag,
                size_bytes=size,
                content_type=content_type,
            )
        except ClientError as exc:
            raise StorageError(key, "upload", str(exc)) from exc

    def download_asset(self, key: str) -> bytes:
        try:
            resp = self._s3.get_object(Bucket=self._bucket, Key=key)
            data: bytes = resp["Body"].read()
            logger.debug("r2 download key={} bytes={}", key, len(data))
            return data
        except ClientError as exc:
            raise StorageError(key, "download", str(exc)) from exc

    def asset_exists(self, key: str) -> bool:
        try:
            self._s3.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise StorageError(key, "exists", str(exc)) from exc

    def list_backgrounds(self, niche_id: str) -> list[BackgroundAsset]:
        prefix = f"backgrounds/{niche_id}/"
        try:
            resp = self._s3.list_objects_v2(Bucket=self._bucket, Prefix=prefix)
            return [
                BackgroundAsset(
                    key=obj["Key"],
                    niche_id=niche_id,
                    filename=str(obj["Key"]).rsplit("/", 1)[-1],
                )
                for obj in resp.get("Contents", [])
            ]
        except ClientError as exc:
            raise StorageError(prefix, "list", str(exc)) from exc

    def delete_asset(self, key: str) -> None:
        try:
            self._s3.delete_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            raise StorageError(key, "delete", str(exc)) from exc


def build_r2_client() -> R2Client:
    return R2Client(
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        bucket=os.environ["R2_BUCKET"],
    )
