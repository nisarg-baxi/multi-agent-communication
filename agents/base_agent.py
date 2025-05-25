import zmq.asyncio
import asyncio
import logging
from config import MESSAGE_TYPES
from .message import Message

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self, context, endpoint):
        self.context = context
        self.endpoint = endpoint
        self.socket = None
        self.running = False

    async def start(self):
        """Start the agent and initialize its socket"""
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.setsockopt(zmq.LINGER, 0)
        try:
            self.socket.bind(self.endpoint)
            logger.info(f"Successfully bound to {self.endpoint}")
        except zmq.error.ZMQError as e:
            logger.error(f"Failed to bind to {self.endpoint}: {str(e)}")
            raise
        self.running = True
        asyncio.create_task(self._receive_messages())

    async def stop(self):
        """Stop the agent and clean up resources"""
        self.running = False
        if self.socket:
            self.socket.close()

    async def send_message(self, message):
        """Send a message to another agent"""
        if not self.socket:
            raise RuntimeError("Agent not started")
        try:
            await self.socket.send_json({
                "type": message.msg_type,
                "content": message.content,
                "sender": message.sender,
                "receiver": message.receiver
            })
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise

    async def _receive_messages(self):
        """Continuously receive and process messages"""
        while self.running:
            try:
                data = await self.socket.recv_json()
                message = Message(
                    msg_type=data["type"],
                    content=data["content"],
                    sender=data.get("sender"),
                    receiver=data.get("receiver")
                )
                await self.handle_message(message)
            except Exception as e:
                logger.error(f"Error receiving message: {str(e)}")
                await asyncio.sleep(1)

    async def handle_message(self, message):
        """Handle incoming messages - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement handle_message")