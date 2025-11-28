# coreliaOS/asgi.py

import os
import logging
from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coreliaOS.settings')

logger = logging.getLogger(__name__)
logger.info("🚀 ASGI application loaded")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # You can add "websocket": AuthMiddlewareStack(...) later
})
