import re

from sqlalchemy.orm import Session

from app.models import Feed
from app.utils.dt import utc_now


class FLoader:
    """F Loader - loads data into the database."""

    # files like: srml-8-2012-results.xml  (competition 8=EPL, 1=Championship)
    _PATTERN_F1 = re.compile(r'^srml-([18])-(\d{4})-results\.xml$')
    # files like: opta-2561896-matchpreview.xml
    _PATTERN_F2 = re.compile(r'^opta-(\d+)-matchpreview\.xml$')
    # files like: srml-8-1-standings.xml
    _PATTERN_F3 = re.compile(r'^srml-([18])-(\d{1,2})-standings\.xml$')
    # files like: srml-8-7-f44348-matchresults.xml
    _PATTERN_F7 = re.compile(r'^srml-([18])-(\d{1,2})-f\d+-matchresults\.xml$')
    # files like: football_results.8.20060917.235959.xml
    _PATTERN_F26 = re.compile(r'^football_results\.([18])\.(\d{8})\.(\d{6})\.xml$')
    # files like: srml-8-10-squads.xml
    _PATTERN_F40 = re.compile(r'^srml-([18])-(\d{1,2})-squads\.xml$')
    # files like: f42-8-2026-results.xml  (competition 8=EPL, 1=Championship)
    _PATTERN_F42 = re.compile(r'^f42-([18])-(\d{4})-results\.xml$')
    # files like: f45-8-2024-venues.xml  (competition 8=EPL, 1=Championship)
    _PATTERN_F45 = re.compile(r'^f45-([18])-(\d{4})-venues\.xml$')

    @staticmethod
    def is_xml_file(blob_name: str) -> bool:
        """Check if the blob name is an XML file."""
        return blob_name.lower().endswith('.xml')

    @staticmethod
    def get_feed_type(blob_name: str) -> str:
        """Determine the feed type based on the blob name."""
        if FLoader._PATTERN_F7.match(blob_name):
            return "f7"
        elif FLoader._PATTERN_F42.match(blob_name):
            return "f42"
        elif FLoader._PATTERN_F45.match(blob_name):
            return "f45"
        elif FLoader._PATTERN_F1.match(blob_name):
            return "f1"
        elif FLoader._PATTERN_F2.match(blob_name):
            return "f2"
        elif FLoader._PATTERN_F3.match(blob_name):
            return "f3"
        elif FLoader._PATTERN_F40.match(blob_name):
            return "f40"
        elif FLoader._PATTERN_F26.match(blob_name):
            return "f26"
        else:
            return ""

    @staticmethod
    def log_feed_start(db: Session, blob_name: str) -> Feed:
        """Insert or update a Feed row at the start of processing."""
        start = utc_now()
        existing = db.query(Feed).filter(Feed.feedName == blob_name).first()
        if existing:
            existing.versions += 1
            existing.startDate = start
            existing.endDate = None
            existing.duration = None
            existing.updatedIn = start
            db.commit()
            db.refresh(existing)
            return existing
        feed = Feed(
            feedName=blob_name,
            feedType=FLoader.get_feed_type(blob_name),
            versions=1,
            startDate=start,
            createdIn=start,
        )
        db.add(feed)
        db.commit()
        db.refresh(feed)
        return feed

    @staticmethod
    def log_feed_end(db: Session, feed: Feed) -> None:
        """Stamp endDate and duration once processing is done."""
        end = utc_now()
        feed.endDate = end
        feed.duration = (end - feed.startDate).total_seconds()
        feed.updatedIn = end
        db.commit()