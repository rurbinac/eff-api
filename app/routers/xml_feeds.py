# ruff: noqa: BLE001  – broad Exception catches are intentional in Pub/Sub handlers
import base64
import json
import logging

from fastapi import APIRouter, Header, HTTPException, Request
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.database import DbSession
from app.services.f_loader import FLoader
from app.services.xml_feeds import XmlFeedsStorage

logger = logging.getLogger(__name__)

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
    logger.info("xml_feed_notify: blob=%s event_type=%s", blob_name, gcs_event.get("eventType", gcs_event.get("kind", "?")))
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
        logger.error("xml_feed_notify: GCS read failed: %s", e)
        return {"status": "error", "file": blob_name, "error": f"GCS read failed: {e!s}"}

    # Create/reset the Process tracking row; returns None when content is unchanged
    try:
        process = FLoader.log_feed_start(db, blob_name, content)
    except Exception:
        logger.exception("xml_feed_notify: log_feed_start failed for %s", blob_name)
        process = None

    if process is None:
        logger.info("xml_feed_notify: skipped %s (identical content or process init error)", blob_name)
        return {"status": "skipped", "reason": "identical content or process init error", "file": blob_name}

    logger.info("xml_feed_notify: log_feed_start returned process_id=%s", process.process_id)
    try:
        tmp_name = FLoader.create_temp_file(content)
        process = FLoader.load_file(db, process, tmp_name)
    finally:
        FLoader.delete_temp_file(tmp_name)

    logger.info("xml_feed_notify: done process_id=%s finishDate=%s tasks=%s", process.process_id, process.finishDate, process.tasks)
    return {
        "status": "processed",
        "bucket": bucket,
        "file": process.process_name,
        "feed_type": feed_type,
        "process_id": process.process_id,
        "versions": process.versions,
        "duration_secs": process.duration,
        "tasks": process.tasks,
    }
