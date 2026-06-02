from fastapi import FastAPI
from app.routers import auth, legacy
from app.database import Base, engine

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="EFF API")

# Include routers
app.include_router(auth.router)
app.include_router(legacy.router)


@app.get("/health")
def health():
    return {"status": "ok"}
