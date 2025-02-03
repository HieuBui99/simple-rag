from fastapi import FastAPI
from fastapi import Request

app = FastAPI()

@app.get("/health_check")
async def health_check(request: Request):
    return {"status": "ok"}