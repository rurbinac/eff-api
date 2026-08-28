# ruff: noqa: BLE001  – broad Exception catches are intentional in Pub/Sub handlers
import base64
import json
import os
import tempfile

from fastapi import APIRouter, Header, HTTPException, Request
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.database import DbSession
from app.services.f42_loader import F42Loader
from app.services.f7_loader import F7Loader
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
    bucket: str = gcs_event.get("bucket", "")

    # Determine feed type - empty string means unrecognised
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

    # Open a Feeds log row
    feed_row = FLoader.log_feed_start(db, blob_name)

    # Write to a temp file (parsers take a file path, not bytes) and process
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        if feed_type == "f42":
            result = F42Loader.load_file(db, tmp_path)
        elif feed_type == "f7":
            result = F7Loader.load_file(db, tmp_path, mode="quick")
        else:
            result = {"status": "not_implemented", "feed_type": feed_type}

    except Exception as e:
        result = {"status": "error", "error": str(e)}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # Stamp end time and duration
    FLoader.log_feed_end(db, feed_row)

    return {
        "status": "processed",
        "bucket": bucket,
        "file": blob_name,
        "feed_type": feed_type,
        "feed_id": feed_row.feedID,
        "versions": feed_row.versions,
        "duration_secs": feed_row.duration,
        "result": result,
    }
