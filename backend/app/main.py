from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db import init_db
from app.gateway.router import router as gateway_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="企业微信客服机器人",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(gateway_router)
