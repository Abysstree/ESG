from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import companies, health, imports, jobs, llm, roles, search
from app.db.database import create_db_and_tables


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="EmploymentSkillsGuide API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_origin_regex=r"chrome-extension://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(imports.router, prefix="/api")
    app.include_router(jobs.router, prefix="/api")
    app.include_router(companies.router, prefix="/api")
    app.include_router(llm.router, prefix="/api")
    app.include_router(search.router, prefix="/api")
    app.include_router(roles.router, prefix="/api")

    return app


app = create_app()
