from fastapi import APIRouter

from app.api.v1 import admin, auth, issues, search, social

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(issues.router)
api_router.include_router(search.router)
api_router.include_router(admin.router)
api_router.include_router(social.comments_router)
api_router.include_router(social.photos_router)
api_router.include_router(social.notifications_router)
