from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.buyers import router as buyers_router
from app.api.v1.farmers import router as farmers_router
from app.api.v1.admin import router as admin_router
from app.api.v1.payments import router as payments_router
from app.api.v1.disputes import router as disputes_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.tracking import router as tracking_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(buyers_router)
router.include_router(farmers_router)
router.include_router(admin_router)
router.include_router(payments_router)
router.include_router(disputes_router)
router.include_router(uploads_router)
router.include_router(tracking_router)
