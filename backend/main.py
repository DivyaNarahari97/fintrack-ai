from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import create_tables
from routers import statements, transactions, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(title="Personal Finance Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(statements.router, prefix="/statements", tags=["statements"])
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])


@app.get("/health")
async def health():
    return {"status": "ok"}
