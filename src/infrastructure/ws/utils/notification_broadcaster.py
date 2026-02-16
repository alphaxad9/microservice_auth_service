# src/infrastructure/ws/utils/notification_broadcaster.py

import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from typing import Dict, Any
from uuid import UUID

logger = logging.getLogger(__name__)


class NotificationBroadcaster:
    """
    A thin abstraction around Django Channels for broadcasting
    user-level and room-level WebSocket notifications.
    """

    def __init__(self):
        self.channel_layer = get_channel_layer()

    def send_to_user(self, user_id: UUID, data: Dict[str, Any]):
        """
        Send a notification event to a specific user's global WebSocket group.
        """
        try:
            group_name = f"user_{user_id}"
            async_to_sync(self.channel_layer.group_send)(
                group_name,
                {
                    "type": "user.event",
                    "data": data,
                },
            )
            logger.debug(f"Sent global notification to {group_name}: {data}")
        except Exception as e:
            logger.exception(f"Failed to send global notification to {user_id}: {e}")

    def broadcast_to_room(self, chatroom_id: UUID, data: Dict[str, Any]):
        """
        Broadcast a notification to all WebSocket consumers in a chat room group.
        Assumes room groups are named as 'room_{chatroom_id}'.
        """
        try:
            group_name = f"room_{chatroom_id}"
            async_to_sync(self.channel_layer.group_send)(
                group_name,
                {
                    "type": "room.event",
                    "data": data,
                },
            )
            logger.debug(f"Broadcast room notification to {group_name}: {data}")
        except Exception as e:
            logger.exception(f"Failed to broadcast to room {chatroom_id}: {e}")