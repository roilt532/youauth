from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from pytest_mock import MockerFixture

from alvaro.storage._types import AssetMeta, BackgroundAsset, StorageError
from alvaro.storage.r2 import R2Client, build_r2_client


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": "test"}}, "op")


@pytest.fixture
def mock_boto3(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("alvaro.storage.r2.boto3")


@pytest.fixture
def r2(mock_boto3: MagicMock) -> R2Client:
    return R2Client(
        endpoint_url="https://test.r2.example.com",
        access_key_id="key",
        secret_access_key="s3cr3t",  # noqa: S106
        bucket="test-bucket",
    )


@pytest.fixture
def s3(mock_boto3: MagicMock) -> MagicMock:
    return mock_boto3.client.return_value


class TestUploadAsset:
    def test_returns_asset_meta(self, r2: R2Client, s3: MagicMock) -> None:
        s3.head_object.return_value = {"ETag": '"abc123"', "ContentLength": 5}
        meta = r2.upload_asset("videos/v.mp4", b"hello", "video/mp4")
        assert isinstance(meta, AssetMeta)
        assert meta.etag == "abc123"
        assert meta.size_bytes == 5
        assert meta.bucket == "test-bucket"

    def test_calls_put_object(self, r2: R2Client, s3: MagicMock) -> None:
        s3.head_object.return_value = {"ETag": '"e"', "ContentLength": 4}
        r2.upload_asset("k", b"data", "application/octet-stream")
        s3.put_object.assert_called_once_with(
            Bucket="test-bucket", Key="k", Body=b"data", ContentType="application/octet-stream"
        )

    def test_raises_storage_error_on_client_error(self, r2: R2Client, s3: MagicMock) -> None:
        s3.put_object.side_effect = _client_error("InternalError")
        with pytest.raises(StorageError) as exc_info:
            r2.upload_asset("k", b"", "video/mp4")
        assert exc_info.value.operation == "upload"


class TestDownloadAsset:
    def test_returns_bytes(self, r2: R2Client, s3: MagicMock) -> None:
        s3.get_object.return_value = {"Body": MagicMock(read=lambda: b"content")}
        data = r2.download_asset("videos/v.mp4")
        assert data == b"content"

    def test_raises_storage_error(self, r2: R2Client, s3: MagicMock) -> None:
        s3.get_object.side_effect = _client_error("NoSuchKey")
        with pytest.raises(StorageError) as exc_info:
            r2.download_asset("missing.mp4")
        assert exc_info.value.operation == "download"


class TestAssetExists:
    def test_true_when_head_succeeds(self, r2: R2Client, s3: MagicMock) -> None:
        s3.head_object.return_value = {}
        assert r2.asset_exists("k") is True

    def test_false_on_404(self, r2: R2Client, s3: MagicMock) -> None:
        s3.head_object.side_effect = _client_error("404")
        assert r2.asset_exists("k") is False

    def test_raises_on_other_error(self, r2: R2Client, s3: MagicMock) -> None:
        s3.head_object.side_effect = _client_error("AccessDenied")
        with pytest.raises(StorageError):
            r2.asset_exists("k")


class TestListBackgrounds:
    def test_returns_background_assets(self, r2: R2Client, s3: MagicMock) -> None:
        s3.list_objects_v2.return_value = {
            "Contents": [{"Key": "backgrounds/science/a.mp4"}, {"Key": "backgrounds/science/b.mp4"}]
        }
        result = r2.list_backgrounds("science")
        assert len(result) == 2
        assert all(isinstance(a, BackgroundAsset) for a in result)
        assert result[0].niche_id == "science"
        assert result[0].filename == "a.mp4"

    def test_empty_when_no_contents(self, r2: R2Client, s3: MagicMock) -> None:
        s3.list_objects_v2.return_value = {}
        assert r2.list_backgrounds("science") == []

    def test_uses_correct_prefix(self, r2: R2Client, s3: MagicMock) -> None:
        s3.list_objects_v2.return_value = {}
        r2.list_backgrounds("history")
        s3.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket", Prefix="backgrounds/history/"
        )


class TestBuildR2Client:
    def test_reads_env(self, monkeypatch: pytest.MonkeyPatch, mock_boto3: MagicMock) -> None:
        monkeypatch.setenv("R2_ENDPOINT_URL", "https://r2.example.com")
        monkeypatch.setenv("R2_ACCESS_KEY_ID", "kid")
        monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "secret")
        monkeypatch.setenv("R2_BUCKET", "mybucket")
        client = build_r2_client()
        assert client._bucket == "mybucket"

    def test_missing_env_raises(
        self, monkeypatch: pytest.MonkeyPatch, mock_boto3: MagicMock
    ) -> None:
        monkeypatch.delenv("R2_ENDPOINT_URL", raising=False)
        with pytest.raises(KeyError):
            build_r2_client()
