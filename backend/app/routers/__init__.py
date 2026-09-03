from .auth import router as auth_router
from .patients import router as patients_router
from .upload import router as upload_router
from .viewer import router as viewer_router
from .wearables import router as wearables_router

__all__ = [
    "auth_router",
    "patients_router",
    "upload_router",
    "viewer_router",
    "wearables_router"
]
