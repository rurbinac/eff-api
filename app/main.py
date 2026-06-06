from fastapi import FastAPI
from app.routers import auth, legacy, leagues, divisions, teams, division_notes, lookups, real_matches, team_standings, real_standings, matches, match_teams, real_team_standings, gaming_api, team_member_transfers

app = FastAPI(title="EFF API")

# Include routers
app.include_router(auth.router)
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
app.include_router(gaming_api.router)
app.include_router(team_member_transfers.router)


@app.get("/health")
def health():
    return {"status": "ok"}
