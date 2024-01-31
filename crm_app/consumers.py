from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
import json
from asgiref.sync import async_to_sync
from .models import ChatGroup, ChatMessage, Employee


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        
        self.group_name = self.scope["url_route"]["kwargs"]["group_id"]
        self.user = self.scope["user"]

        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)

        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        print("Message receive from client", text_data)
        data = json.loads(text_data)
        
        if "msg" in data:
            message = data["msg"]
            username = self.user.first_name + " " + self.user.last_name
            group = ChatGroup.objects.get(id=self.group_name)
            chat = ChatMessage(
                message_content=data["msg"], group=group, message_by=self.user
            )
            chat.save()
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {"type": "chat.message", "message": message, "message_by": username},
            )
        elif "attachment" in data:
            # Handle attachments
            attachment = data["attachment"]
            filename = attachment.get("filename", "")
            file_data = attachment.get("data", "")

            # Save the attachment to the database
            group = ChatGroup.objects.get(id=self.group_name)
            chat = ChatMessage(
                group=group,
                message_by=self.user,
                filename=filename,
                attachment=file_data,
            )
            chat.save()

            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "chat.attachment",
                    "filename": filename,
                    "message_by": self.user.first_name + " " + self.user.last_name,
                    "data": file_data,
                },
            )

    def chat_message(self, event):
        self.send(
            text_data=json.dumps(
                {"msg": event["message"], "msg_by": event["message_by"]}
            )
        )

    def chat_attachment(self, event):
        
        self.send(
            text_data=json.dumps(
                {
                    "attachment": {
                        "filename": event["filename"],
                        "msg_by": event["message_by"],
                        "data": event["data"],
                    }
                }
            )
        )

    def disconnect(self, code):
        print("Websocket Disconnected...", code)


#  --------------------------- Notification ----------------------


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # Add the user to the "employees_group" group
        self.employee_id = self.scope["url_route"]["kwargs"]["employee_id"]
        print("helooooo connection...")
        await self.channel_layer.group_add(self.employee_id, self.channel_name)

    async def disconnect(self, close_code):
        # Remove the user from the "employees_group" group
        await self.channel_layer.group_discard(self.employee_id, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        message = text_data_json["message"]

        # Send the received message to the client
        await self.send(text_data=json.dumps({"message": message}))

    # Custom method to handle notifications
    async def notify(self, event):
        message = event["message"]
        count = event["count"]

        # Send the notification to the client
        await self.send(text_data=json.dumps({"message": message, "count": count}))

    async def assign(self, event):
        message = event["message"]
        count = event["count"]

        # Send the notification to the client
        await self.send(text_data=json.dumps({"message": message, "count": count}))


class NotificationAgentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # Add the user to the "employees_group" group
        self.agent_id = self.scope["url_route"]["kwargs"]["agent_id"]
        print("helooooo connection...")
        await self.channel_layer.group_add(self.agent_id, self.channel_name)

    async def disconnect(self, close_code):
        # Remove the user from the "employees_group" group
        await self.channel_layer.group_discard(self.agent_id, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        print("Message receive from client", text_data)
        message = text_data_json["message"]

        # Send the received message to the client
        await self.send(text_data=json.dumps({"message": message}))

    # Custom method to handle notifications
    async def notify(self, event):
        message = event["message"]
        count = event["count"]

        # Send the notification to the client
        await self.send(text_data=json.dumps({"message": message, "count": count}))

    async def assign(self, event):
        message = event["message"]
        count = event["count"]

        # Send the notification to the client
        await self.send(text_data=json.dumps({"message": message, "count": count}))

    async def assignop(self, event):
        message = event["message"]
        count = event["count"]

        # Send the notification to the client
        await self.send(text_data=json.dumps({"message": message, "count": count}))


# ------------------------------------------------------------------------


class NotificationAdminConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # Add the user to the "employees_group" group

        print("helooooo admin connection...")
        await self.channel_layer.group_add("admin_group", self.channel_name)

    async def disconnect(self, close_code):
        # Remove the user from the "employees_group" group
        await self.channel_layer.group_discard("admin_group", self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        print("Message receive from client", text_data)
        message = text_data_json["message"]

        # Send the received message to the client
        await self.send(text_data=json.dumps({"message": message}))

    # Custom method to handle notifications
    async def notify_admin(self, event):
        message = event["message"]
        count = event["count"]

        # Send the notification to the client
        await self.send(text_data=json.dumps({"message": message, "count": count}))
