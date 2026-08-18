import base64
import json
import re

from fastapi import APIRouter, Header, HTTPException, Request
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

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
    authorization: str | None = Header(None),
):
    _verify_pubsub_token(authorization)

    body = await request.json()
    message = body.get("message", {})
    data_b64 = message.get("data", "")
    gcs_event = json.loads(base64.b64decode(data_b64).decode("utf-8"))

    blob_name: str = gcs_event.get("name", "")
    bucket: str = gcs_event.get("bucket", "")

    # files like: f42-8-2026-results.xml
    pattern_f42 = r'^f42-([18])-(\d{4})-results\.xml$'
    # files like: srml-8-7-f44348-matchresults.xml
    pattern_f7 = r'^srml-([18])-(\d{1,2})-f\d+-matchresults\.xml$'
    if re.match(pattern_f42, blob_name):
        pass # Process f42 files
    elif re.match(pattern_f7, blob_name):
        pass # Process f7 files
    else:
        return {"status": "ignored", "reason": "filename does not match expected patterns"}

    # TODO: process the file — read from GCS via XmlFeedsStorage and parse
    # from app.services.xml_feeds import XmlFeedsStorage
    # content = XmlFeedsStorage.read_file_text(blob_name)
    # ...

    return {"status": "received", "bucket": bucket, "file": blob_name}
