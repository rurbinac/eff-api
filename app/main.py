from fastapi import FastAPI

app = FastAPI(title="EFF API")


@app.get("/health")
def health():
    return {"status": "ok"}
