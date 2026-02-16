# src/infrastructure/ws/async_notification_broadcaster.py
from typing import Dict, Any
from channels.layers import get_channel_layer
import logging
from uuid import UUID
logger = logging.getLogger(__name__)

class AsyncNotificationBroadcaster:
    """
    Async wrapper around Channels channel_layer for use in async event handlers.
    """

    def __init__(self):
        self.channel_layer = get_channel_layer()

    async def send_to_user(self, user_id: UUID, data: Dict[str, Any]):
        """
        Send a notification to a specific user's global group.
        Group name convention: user_{user_id}
        """
        try:
            group_name = f"user_{user_id}"
            await self.channel_layer.group_send(
                group_name,
                {
                    "type": "user.event",  # consumer will implement user_event handler
                    "data": data,
                },
            )
            logger.debug("async: sent user notification to %s: %s", group_name, data)
        except Exception as e:
            logger.exception("async: failed to send to user %s: %s", user_id, e)

    async def broadcast_to_room(self, chatroom_id: UUID, data: Dict[str, Any]):
        """
        Broadcast to all members connected to the room group.
        Group name convention: room_{chatroom_id}
        """
        try:
            group_name = f"room_{chatroom_id}"
            await self.channel_layer.group_send(
                group_name,
                {
                    "type": "room.event",  # consumer will implement room_event handler
                    "data": data,
                },
            )
            logger.debug("async: broadcast to room %s: %s", group_name, data)
        except Exception as e:
            logger.exception("async: failed to broadcast to room %s: %s", chatroom_id, e)
