"""API模块"""

from .certificate_routes import router as certificate_router
from .chat_routes import router as chat_router
from .document_routes import router as document_router
from .system_routes import router as system_router
from .prompt_routes import router as prompt_router

__all__ = [
    "certificate_router",
    "chat_router", 
    "document_router",
    "system_router",
    "prompt_router"
]