import hashlib
import os
import re
import tempfile
import time
from enum import StrEnum
from typing import ClassVar

from sqlalchemy.orm import Session

from app.services.f7_loader import F7Loader
from app.services.f42_loader import F42Loader
from app.utils.processes import Process


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

    # Tracks wall-clock start time (perf_counter) per feedID for accurate duration measurement.
    # utc_now() truncates to seconds, so (endDate - startDate) would be 0 for sub-second runs.
    _start_times: ClassVar[dict[int, float]] = {}

    # files like: srml-8-2012-results.xml  (competition 8=EPL, 1=Championship)
    _PATTERN_F1 = re.compile(r"^srml-([18])-(\d{4})-results\.xml$")
    # files like: opta-2561896-matchpreview.xml
    _PATTERN_F2 = re.compile(r"^opta-(\d+)-matchpreview\.xml$")
    # files like: srml-8-1-standings.xml
    _PATTERN_F3 = re.compile(r"^srml-([18])-(\d{4})-standings\.xml$")
    # files like: srml-8-7-f44348-matchresults.xml  or  srml-8-2026-f2645232-matchresults.xml
    _PATTERN_F7 = re.compile(r"^srml-([18])-(\d+)-f\d+-matchresults\.xml$")
    # files like: football_results.8.20060917.235959.xml
    _PATTERN_F26 = re.compile(r"^football_results\.([18])\.(\d{8})\.(\d{6})\.xml$")
    # files like: srml-8-10-squads.xml
    _PATTERN_F40 = re.compile(r"^srml-([18])-(\d{4})-squads\.xml$")
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
    ) -> Process | None:
        """Get or create a Process for this feed file.

        Returns None if the file's sha256 is unchanged since the last run (unless force=True).
        Resets the existing process record when the content has changed.
        """
        file_sha256 = hashlib.sha256(content).digest()
        feed_type = FLoader.get_feed_type(blob_name)
        process = Process.init_feeds_process(db, feed_type, blob_name)

        if not force and process.sha256 == file_sha256:
            return None

        process.reset(sha256=file_sha256)
        db.commit()
        FLoader._start_times[process.process_id] = time.perf_counter()
        return process

    @staticmethod
    def log_feed_end(db: Session, process: Process) -> Process:
        """Finish the process, persist finishDate/duration/tasks, and commit."""
        FLoader._start_times.pop(process.process_id, None)
        process.finish()
        try:
            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
            db.commit()
        return process

    @staticmethod
    def create_temp_file(content: bytes) -> str:
        tmp_path: str | None = None
        # Parsers expect a file path, so write content to a temp file
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        return tmp_path

    @staticmethod
    def delete_temp_file(tmp_name: str) -> None:
        if tmp_name and os.path.exists(tmp_name):
            os.unlink(tmp_name)

    @staticmethod
    def load_file(db: Session, process: Process, tmp_name: str | None = None) -> Process:
        """Download, parse, and persist a feed file; finish the Process when done.

        Args:
            db:       Database session
            process:  Process row (already created by log_feed_start)
            tmp_name: Path to the temporary file containing the feed data
        """
        feed_type = FLoader.get_feed_type(process.process_name)
        try:
            match feed_type:
                case FeedTypes.F42:
                    return F42Loader.load_file(db, process=process, tmp_name=tmp_name)
                case FeedTypes.F7:
                    return F7Loader.load_file(db, process=process, tmp_name=tmp_name)
                case _:
                    task = process.create_task(f"Load {feed_type} file: {process.process_name}")
                    task.add_error(f"No loader implemented for feed type '{feed_type}'")
                    task.close(status=task.ERROR)

        except Exception as e:  # noqa: BLE001
            process._tasks = [{"status": "error", "error": str(e)}]

        finally:
            FLoader.delete_temp_file(tmp_name)

        return FLoader.log_feed_end(db, process)
