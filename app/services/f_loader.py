import hashlib
import os
import re
import tempfile
from enum import StrEnum

from sqlalchemy.orm import Session

from app.models import Feed
from app.services.f7_loader import F7Loader
from app.services.f42_loader import F42Loader
from app.utils.dt import utc_now


class FeedTypes(StrEnum):
    F1 = "f1"
    F2 = "f2"
    F3 = "f3"
    F7 = "f7"
    F26 = "f26"
    F40 = "f40"
    F42 = "f42"
    F45 = "f45"
    UNKNOWN = "?"
    NOT_XML = ""


class FLoader:
    """Central dispatcher for OPTA XML feed files."""

    # files like: srml-8-2012-results.xml  (competition 8=EPL, 1=Championship)
    _PATTERN_F1 = re.compile(r"^srml-([18])-(\d{4})-results\.xml$")
    # files like: opta-2561896-matchpreview.xml
    _PATTERN_F2 = re.compile(r"^opta-(\d+)-matchpreview\.xml$")
    # files like: srml-8-1-standings.xml
    _PATTERN_F3 = re.compile(r"^srml-([18])-(\d{1,2})-standings\.xml$")
    # files like: srml-8-7-f44348-matchresults.xml
    _PATTERN_F7 = re.compile(r"^srml-([18])-(\d{1,2})-f\d+-matchresults\.xml$")
    # files like: football_results.8.20060917.235959.xml
    _PATTERN_F26 = re.compile(r"^football_results\.([18])\.(\d{8})\.(\d{6})\.xml$")
    # files like: srml-8-10-squads.xml
    _PATTERN_F40 = re.compile(r"^srml-([18])-(\d{1,2})-squads\.xml$")
    # files like: f42-8-2026-results.xml  (competition 8=EPL, 1=Championship)
    _PATTERN_F42 = re.compile(r"^f42-([18])-(\d{4})-results\.xml$")
    # files like: f45-8-2024-venues.xml  (competition 8=EPL, 1=Championship)
    _PATTERN_F45 = re.compile(r"^f45-([18])-(\d{4})-venues\.xml$")

    @staticmethod
    def is_xml_file(blob_name: str) -> bool:
        """Check if the blob name is an XML file."""
        return blob_name.lower().endswith(".xml")

    @staticmethod
    def get_feed_type(blob_name: str) -> FeedTypes:
        """Determine the feed type from the filename. Returns '' if unrecognised."""
        if FLoader._PATTERN_F7.match(blob_name):
            return FeedTypes.F7
        elif FLoader._PATTERN_F42.match(blob_name):
            return FeedTypes.F42
        elif FLoader._PATTERN_F1.match(blob_name):
            return FeedTypes.F1
        elif FLoader._PATTERN_F2.match(blob_name):
            return FeedTypes.F2
        elif FLoader._PATTERN_F3.match(blob_name):
            return FeedTypes.F3
        elif FLoader._PATTERN_F26.match(blob_name):
            return FeedTypes.F26
        elif FLoader._PATTERN_F40.match(blob_name):
            return FeedTypes.F40
        elif FLoader._PATTERN_F45.match(blob_name):
            return FeedTypes.F45
        else:
            return (
                FeedTypes.UNKNOWN
                if blob_name.lower().endswith(".xml")
                else FeedTypes.NOT_XML
            )

    @staticmethod
    def log_feed_start(
        db: Session, blob_name: str, content: bytes, force: bool = False
    ) -> Feed | None:
        """Insert or update a Feed row at the start of processing.

        Computes size, cumulative totalSize, and sha256 from the raw file bytes.
        """
        start = utc_now()
        file_size = len(content)
        file_sha256 = hashlib.sha256(content).digest()  # 32 bytes

        feed = db.query(Feed).filter(Feed.feedName == blob_name).first()
        file_changed = not feed or feed.sha256 != file_sha256 or feed.size != file_size
        if feed:
            feed.versions += 1
            feed.updatedIn = start
            if file_changed or force:
                # Content is different (or forced) — reset processing fields and reprocess
                feed.startDate = start
                feed.endDate = None
                feed.duration = None
                feed.size = file_size
                feed.totalSize += file_size
                feed.sha256 = file_sha256
            # else: content identical — only versions/updatedIn bumped; caller receives None
        else:
            feed = Feed(
                feedName=blob_name,
                feedType=FLoader.get_feed_type(blob_name),
                versions=1,
                startDate=start,
                size=file_size,
                totalSize=file_size,
                sha256=file_sha256,
                createdIn=start,
            )
            db.add(feed)
        db.commit()
        db.refresh(feed)
        return feed if file_changed or force else None

    @staticmethod
    def log_feed_end(db: Session, feed: Feed, result: dict | None = None) -> None:
        """Stamp endDate, duration, and results once processing is done."""
        end = utc_now()
        feed.endDate = end
        feed.duration = (end - feed.startDate).total_seconds()
        feed.updatedIn = end
        if result is not None:
            feed.results = result
        db.commit()

    @staticmethod
    def create_temp_file(content: bytes) -> str:
        tmp_path: str | None = None
        # Parsers expect a file path, so write content to a temp file
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        return tmp_path

    @staticmethod
    def load_file(db: Session, feed: Feed, tmp_name: str | None = None) -> dict:
        """Download, parse, and persist a feed file; stamp the Feed log row when done.

        Args:
            db:      Database session
            feed:    Feed log row (already created by log_feed_start)
            tmp_name: Path to the temporary file containing the feed data
        """
        try:
            # Parsers expect a file path, so write content to a temp file

            match feed.feedType:
                case FeedTypes.F42:
                    result = F42Loader.load_file(db, feed=feed, tmp_name=tmp_name)
                case FeedTypes.F7:
                    result = F7Loader.load_file(
                        db, feed=feed, tmp_name=tmp_name, quick_mode=True
                    )
                case _:
                    result = {}

        except Exception as e:  # noqa: BLE001
            result = {"status": "error", "error": str(e)}
        finally:
            if tmp_name and os.path.exists(tmp_name):
                os.unlink(tmp_name)

        FLoader.log_feed_end(db, feed, result=result)

        return {
            "status": "processed",
            "file": feed.feedName,
            "feed_type": feed.feedType,
            "feed_id": feed.feedID,
            "versions": feed.versions,
            "duration_secs": feed.duration,
            "result": result,
        }
