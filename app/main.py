"""
Agent Forge Main FastAPI Application Entrypoint.
"""

from fastapi import FastAPI
from app.core.config import settings
from app.api.task_routes import router as task_router
from app.api.architecture_routes import router as architecture_router
from app.api.execution_routes import router as execution_router
from app.api.evaluation_routes import router as evaluation_router
from app.api.memory_routes import router as memory_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Autonomous Multi-Agent Architecture Synthesis and Evolution Framework",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
        "environment": settings.APP_ENV,
        "phase": "Mid-Sem Scaffolding Setup",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
