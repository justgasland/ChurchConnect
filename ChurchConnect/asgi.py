"""
ASGI config for churchconnect project.
Handles both HTTP and WebSocket connections
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'churchconnect.settings')
django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

# Import routing after Django setup
from ChurchConnect.routing import websocket_urlpatterns

# Initialize Django ASGI application early to populate apps
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    # HTTP requests
    "http": django_asgi_app,
    
    # WebSocket requests
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})