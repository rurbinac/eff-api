import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)

from app.routers import (
    admin,
    auth,
    division_notes,
    divisions,
    leagues,
    legacy,
    lookups,
    match_teams,
    matches,
    pusher_auth,
    real_matches,
    real_standings,
    real_team_standings,
    team_member_transfers,
    team_standings,
    teams,
    users,
    xml_feeds,
)

app = FastAPI(title="EFF API")


@app.on_event("startup")
def _migrate_db() -> None:
    """Apply any pending schema changes that create_all cannot handle (column additions)."""
    from sqlalchemy import text
    from app.database import engine
    migrations = [
        # 2026-10-14: prevProcessID added to Processes after initial table creation
        "ALTER TABLE Processes ADD COLUMN prevProcessID INT(11) DEFAULT NULL AFTER processID",
        # 2026-10-14: processID was created without AUTO_INCREMENT
        "ALTER TABLE Processes MODIFY processID INT NOT NULL AUTO_INCREMENT",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass

_cors_origins = ["https://effootball.com"]
if os.getenv("ADMIN_DEV_CORS"):
    _cors_origins.append("http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(users.legacy_router)
app.include_router(legacy.router)
app.include_router(leagues.router)
app.include_router(divisions.router)
app.include_router(teams.router)
app.include_router(division_notes.router)
app.include_router(lookups.router)
app.include_router(real_matches.router)
app.include_router(team_standings.router)
app.include_router(real_standings.router)
app.include_router(matches.router)
app.include_router(match_teams.router)
app.include_router(real_team_standings.router)
app.include_router(team_member_transfers.router)
app.include_router(xml_feeds.router)
app.include_router(pusher_auth.router)


@app.get("/health")
def health():
    return {"status": "ok"}


_admin_dist = os.path.join(os.path.dirname(__file__), "..", "admin", "dist")
if os.path.isdir(_admin_dist):
    app.mount("/admin", StaticFiles(directory=_admin_dist, html=True), name="admin")
