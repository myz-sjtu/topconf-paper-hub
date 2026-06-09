from fastapi import APIRouter

from app.api.routes.conferences import router as conferences_router
from app.api.routes.crawl import router as crawl_router
from app.api.routes.papers import router as papers_router

api_router = APIRouter()
api_router.include_router(conferences_router)
api_router.include_router(papers_router)
api_router.include_router(crawl_router)

__all__ = ["api_router"]

