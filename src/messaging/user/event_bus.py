# Updated Event Bus
import logging
from typing import Dict, List, Type, Callable, Awaitable, Union
from threading import RLock
from dataclasses import dataclass
from abc import ABC, abstractmethod

from src.domain.user.events import UserEvent

logger = logging.getLogger(__name__)

# Update the abstract base class and type hints for async
class BaseEventHandler(ABC):
    @abstractmethod
    async def handle(self, event: UserEvent) -> None:
        raise NotImplementedError

# Define the type for an async handler function
AsyncEventHandlerFunction = Callable[[UserEvent], Awaitable[None]]

@dataclass(frozen=True)
class RegisteredHandler:
    handler: Union[BaseEventHandler, AsyncEventHandlerFunction]
    event_type: Type[UserEvent]


class UserEventBus:
    def __init__(self) -> None:
        self._handlers: Dict[Type[UserEvent], List[RegisteredHandler]] = {}
        self._lock = RLock()

    def subscribe(
        self,
        event_type: Type[UserEvent],
        handler: Union[BaseEventHandler, AsyncEventHandlerFunction],
    ) -> None:
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(RegisteredHandler(handler, event_type))
            logger.debug("Subscribed %s to event %s", handler, event_type.__name__)

    async def publish(self, event: UserEvent) -> None:
        event_type = type(event)
        handlers_to_call: List[RegisteredHandler] = []

        with self._lock:
            if event_type in self._handlers:
                handlers_to_call = list(self._handlers[event_type])

        if not handlers_to_call:
            logger.debug("No handlers for event: %s", event_type.__name__)
            return

        logger.info("Publishing event: %s", event_type.__name__)

        for reg_handler in handlers_to_call:
            try:
                # Await the handler's handle method
                if isinstance(reg_handler.handler, BaseEventHandler):
                    await reg_handler.handler.handle(event)
                # Await the handler function directly
                else:
                    await reg_handler.handler(event)
                logger.debug("Handler %s executed for %s", reg_handler.handler, event_type.__name__)
            except Exception as e:
                logger.error(
                    "Handler %s failed for event %s: %s",
                    reg_handler.handler,
                    event_type.__name__,
                    e,
                    exc_info=True,
                )

    def clear_all_handlers(self) -> None:
        with self._lock:
            self._handlers.clear()
            logger.info("Cleared all event handlers.")

    def get_subscribed_events(self) -> List[Type[UserEvent]]:
        with self._lock:
            return list(self._handlers.keys())
        
userbus = UserEventBus()




