from fastapi import FastAPI
from app.routers import auth, legacy, leagues

app = FastAPI(title="EFF API")

# Include routers
app.include_router(auth.router)
app.include_router(legacy.router)
app.include_router(leagues.router)


@app.get("/health")
def health():
    return {"status": "ok"}
