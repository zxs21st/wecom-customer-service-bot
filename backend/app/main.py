from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db import init_db
from app.gateway.router import router as gateway_router
from app.ai_engine.router import router as ai_router
from app.knowledge.router import router as knowledge_router


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
app.include_router(ai_router)
app.include_router(knowledge_router)
