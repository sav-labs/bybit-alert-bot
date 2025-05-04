from app.handlers.common import router as common_router
from app.handlers.user import router as user_router
from app.handlers.admin import router as admin_router

routers = [common_router, user_router, admin_router]