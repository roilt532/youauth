from __future__ import annotations

import os
import uuid

import pytest

from alvaro.storage.r2 import build_r2_client

pytestmark = pytest.mark.skipif(
    not os.environ.get("R2_ENDPOINT_URL"),
    reason="R2_ENDPOINT_URL not set - skipping integration test",
)


@pytest.fixture(scope="module")
def r2() -> object:
    return build_r2_client()


@pytest.fixture
def test_key() -> str:
    return f"integration-tests/{uuid.uuid4()}.txt"


def test_upload_download_roundtrip(r2: object, test_key: str) -> None:
    from alvaro.storage.r2 import R2Client

    assert isinstance(r2, R2Client)
    payload = b"integration test payload"
    meta = r2.upload_asset(test_key, payload, "text/plain")
    assert meta.size_bytes == len(payload)
    assert len(meta.etag) > 0

    downloaded = r2.download_asset(test_key)
    assert downloaded == payload

    r2.delete_asset(test_key)


def test_asset_exists_true_after_upload(r2: object, test_key: str) -> None:
    from alvaro.storage.r2 import R2Client

    assert isinstance(r2, R2Client)
    r2.upload_asset(test_key, b"x", "text/plain")
    assert r2.asset_exists(test_key) is True
    r2.delete_asset(test_key)


def test_asset_exists_false_after_delete(r2: object, test_key: str) -> None:
    from alvaro.storage.r2 import R2Client

    assert isinstance(r2, R2Client)
    r2.upload_asset(test_key, b"x", "text/plain")
    r2.delete_asset(test_key)
    assert r2.asset_exists(test_key) is False


def test_list_backgrounds_returns_list(r2: object) -> None:
    from alvaro.storage.r2 import R2Client

    assert isinstance(r2, R2Client)
    result = r2.list_backgrounds("science")
    assert isinstance(result, list)
