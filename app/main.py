from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.infrastructure.database import engine, Base, AsyncSessionLocal
from app.infrastructure.schema_check import verify_schema
from app.api import routes_contracts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    # 1. Create all tables (new columns included)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Verify schema version — raises RuntimeError if DB is stale
    async with AsyncSessionLocal() as session:
        await verify_schema(session)

    yield
    # ── Shutdown (nothing to do) ─────────────────────────────────────────────


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(routes_contracts.router, prefix="/api/contracts", tags=["contracts"])


@app.get("/")
def health_check():
    return {"status": "ok", "message": "AI Contract Risk Platform API is running"}
