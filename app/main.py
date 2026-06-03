from fastapi import FastAPI
from app.routers import auth, legacy, leagues, divisions, teams, division_notes

app = FastAPI(title="EFF API")

# Include routers
app.include_router(auth.router)
app.include_router(legacy.router)
app.include_router(leagues.router)
app.include_router(divisions.router)
app.include_router(teams.router)
app.include_router(division_notes.router)


@app.get("/health")
def health():
    return {"status": "ok"}
