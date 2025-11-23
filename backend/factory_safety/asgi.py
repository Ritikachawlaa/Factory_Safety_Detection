"""
ASGI config for factory_safety project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""


import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from django.urls import path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'factory_safety.settings')

# Import consumers if available, else create a placeholder
try:
	from detection_system import consumers
	websocket_routes = [
		path("ws/factory/", consumers.FactoryConsumer.as_asgi()),
	]
except ImportError:
	websocket_routes = []

application = ProtocolTypeRouter({
	"http": get_asgi_application(),
	"websocket": AuthMiddlewareStack(
		URLRouter(websocket_routes)
	),
})
