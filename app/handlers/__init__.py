from app.handlers.common import router as common_router
from app.handlers.user import router as user_router
from app.handlers.admin import router as admin_router

# User router should be first to handle FSM states before common handlers
routers = [user_router, admin_router, common_router]