from fastapi.routing import APIRouter

from apps.api.views.streaming import router as routes

router = APIRouter()

router.include_router(routes)
