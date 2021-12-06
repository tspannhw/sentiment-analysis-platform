# -*- coding: utf-8 -*-

from fastapi.routing import APIRouter

from apps.health_check.urls import router as router_health_check
from apps.api.urls import router as router_api
from apps.token.urls import router as router_token
from apps.oauth2.urls import router as router_oauth2


router = APIRouter()
router.include_router(router_health_check, prefix='/api/v1', tags=['Health Check'])
router.include_router(router_api, prefix='/api/v1', tags=['Core API'])
router.include_router(router_token, prefix='/api/v1', tags=['Token'])
router.include_router(router_oauth2, prefix='/api/v1', tags=['OAuth2'])
