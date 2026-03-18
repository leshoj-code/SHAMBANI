import json
from channels.generic.websocket import AsyncWebsocketConsumer

class OrderConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope.get("user")

        # Reject unauthenticated connections immediately
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.group_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Guard in case connect() closed early and group_name was never set
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def order_notification(self, event):
        await self.send(text_data=json.dumps({
            "type":         "order_request",
            "machine_name": event["machine_name"],
            "order_id":     event["order_id"],
            "renter_name":  event["renter_name"],
        }))

    async def status_update_message(self, event):
        await self.send(text_data=json.dumps({
            "type":         "status_update",
            "machine_name": event["machine_name"],
            "new_status":   event["new_status"],
        }))

    async def renter_message(self, event):
        await self.send(text_data=json.dumps({
            "type":    "notification_alert",
            "message": event["message"],
        }))