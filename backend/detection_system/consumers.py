from channels.generic.websocket import AsyncWebsocketConsumer
import json

class FactoryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({"message": "WebSocket connection established."}))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        # Echo received message for now
        if text_data:
            await self.send(text_data=json.dumps({"echo": text_data}))
