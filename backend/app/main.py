from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import ALLOWED_ORIGINS


app = FastAPI(
    title="GeneRisk API",
    description="AI-assisted HBB variant triage backend",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": "GeneRisk API",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "GeneRisk API",
        "version": "0.1.0",
        "genome_build": "hg38",
    }