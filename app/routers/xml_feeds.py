# ruff: noqa: BLE001  – broad Exception catches are intentional in Pub/Sub handlers
import base64
import json

from fastapi import APIRouter, Header, HTTPException, Request
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.database import DbSession
from app.services.f_loader import FLoader
from app.services.xml_feeds import XmlFeedsStorage

router = APIRouter(tags=["xml_feeds"])

_PUSH_ENDPOINT = "https://eff-api-338220807664.us-central1.run.app/api/v1/xml_feed_notify"
_PUBSUB_SA_EMAIL = "pubsub-xml-feed-push@sublime-scion-499902-m5.iam.gserviceaccount.com"


def _verify_pubsub_token(authorization: str | None) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization[7:]
    try:
        claim = id_token.verify_oauth2_token(
            token, google_requests.Request(), _PUSH_ENDPOINT
        )
        if claim.get("email") != _PUBSUB_SA_EMAIL:
            raise HTTPException(status_code=401, detail="Unexpected token issuer")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/api/v1/xml_feed_notify")
async def xml_feed_notify(
    request: Request,
    db: DbSession,
    authorization: str | None = Header(None),
):
    """Pub/Sub push handler - called by GCS when a new XML feed file arrives."""
    _verify_pubsub_token(authorization)

    # Decode the Pub/Sub push envelope
    try:
        body = await request.json()
        message = body.get("message", {})
        data_b64 = message.get("data", "")
        gcs_event = json.loads(base64.b64decode(data_b64).decode("utf-8"))
    except Exception as e:
        return {"status": "error", "error": f"Failed to parse Pub/Sub message: {e!s}"}

    blob_name: str = gcs_event.get("name", "")
    if not FLoader.is_xml_file(blob_name):
        return {"status": "ignored", "reason": "not an XML file", "file": blob_name}
    bucket: str = gcs_event.get("bucket", "")

    # Determine feed type — empty string means unrecognised
    feed_type = FLoader.get_feed_type(blob_name)
    if not feed_type:
        return {
            "status": "ignored",
            "reason": "filename does not match expected patterns",
            "file": blob_name,
        }

    # Download the file from GCS
    try:
        content: bytes = XmlFeedsStorage.read_file(blob_name)
    except Exception as e:
        return {"status": "error", "file": blob_name, "error": f"GCS read failed: {e!s}"}

    # Open Feed log row (records size + sha256), process, stamp end time
    # Returns None when the file content is identical to the previous version
    feed_row = FLoader.log_feed_start(db, blob_name, content)
    if feed_row is None:
        return {"status": "skipped", "reason": "identical content (sha256 and size unchanged)", "file": blob_name}
    try:
        tmp_name = FLoader.create_temp_file(content)
        feed = FLoader.load_file(db, feed_row, tmp_name)
    finally:
        FLoader.delete_temp_file(tmp_name)

    return {
        "status": "processed",
        "bucket": bucket,
        "file": feed.feedName,
        "feed_type": feed.feedType,
        "feed_id": feed.feedID,
        "versions": feed.versions,
        "duration_secs": feed.duration,
        "results": feed.results,
    }
