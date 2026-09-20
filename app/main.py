"""
Agent Forge Main FastAPI Application Entrypoint.
Updated by Member 4 to add lifespan (DB init), CORS middleware, and all routers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.memory.database import init_db
from app.api.task_routes import router as task_router
from app.api.architecture_routes import router as architecture_router
from app.api.execution_routes import router as execution_router
from app.api.evaluation_routes import router as evaluation_router
from app.api.memory_routes import router as memory_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run database initialization on startup."""
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Autonomous Multi-Agent Architecture Synthesis and Evolution Framework. "
        "Submits tasks → synthesizes dynamic architectures → executes agent teams → "
        "evaluates → reflects → stores evolutionary experience."
    ),
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — allow the Next.js frontend on localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach API routers
app.include_router(task_router)
app.include_router(architecture_router)
app.include_router(execution_router)
app.include_router(evaluation_router)
app.include_router(memory_router)


@app.get("/health", tags=["Health Check"])
async def health_check():
    """Health check endpoint to verify backend server status."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "0.2.0",
        "environment": settings.APP_ENV,
        "phase": "Mid-Sem — Member 4: Memory + API + Frontend",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
