"""GCS XML feed storage — reads and writes feed files in gs://eff-xml-feeds."""

from google.cloud import storage

_BUCKET_NAME = "eff-xml-feeds"


def _client() -> storage.Client:
    return storage.Client()


class XmlFeedsStorage:
    """Read-only access to XML feed files in GCS."""

    @staticmethod
    def list_files(prefix: str | None = None) -> list[str]:
        """Return blob names in the bucket, optionally filtered by prefix."""
        client = _client()
        bucket = client.bucket(_BUCKET_NAME)
        blobs = client.list_blobs(bucket, prefix=prefix)
        return [blob.name for blob in blobs]

    @staticmethod
    def read_file(blob_name: str) -> bytes:
        """Download and return the raw bytes of a feed file."""
        client = _client()
        bucket = client.bucket(_BUCKET_NAME)
        blob = bucket.blob(blob_name)
        return blob.download_as_bytes()

    @staticmethod
    def read_file_text(blob_name: str, encoding: str = "utf-8") -> str:
        """Download and return a feed file as a decoded string."""
        return XmlFeedsStorage.read_file(blob_name).decode(encoding)

    @staticmethod
    def write_file(blob_name: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        """Upload raw bytes to the bucket under blob_name."""
        client = _client()
        bucket = client.bucket(_BUCKET_NAME)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(data, content_type=content_type)
