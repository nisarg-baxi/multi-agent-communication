import zmq.asyncio
import asyncio
import logging
import json
from enum import Enum
from datetime import datetime
from agents.mcp_message import MCPMessage, MCPPerformatives

logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"

class BaseAgent:
    def __init__(self, agent_id, endpoint, is_planner=False):
        """Initialize the base agent with ZMQ context and socket"""
        self.agent_id = agent_id
        self.endpoint = endpoint
        self.context = zmq.asyncio.Context()
        
        # Use ROUTER for planner, DEALER for other agents
        socket_type = zmq.ROUTER if is_planner else zmq.DEALER
        self.socket = self.context.socket(socket_type)
        
        self.is_planner = is_planner
        self.running = False
        self.connection_state = ConnectionState.DISCONNECTED
        self.connected_agents = set()
        
        # Set identity for non-planner agents
        if not is_planner:
            self.socket.setsockopt_string(zmq.IDENTITY, agent_id)
        
        logger.info(f"Initialized {agent_id} agent with endpoint {endpoint}")

    async def start(self):
        """Start the agent and establish connection"""
        try:
            if self.is_planner:
                logger.info(f"{self.agent_id} binding to {self.endpoint}")
                self.socket.bind(self.endpoint)
            else:
                logger.info(f"{self.agent_id} connecting to {self.endpoint}")
                self.socket.connect(self.endpoint)
            
            self.running = True
            self.connection_state = ConnectionState.CONNECTING
            
            # Start message receiver
            asyncio.create_task(self._receive_messages())
            logger.info(f"{self.agent_id} message receiver started")
            
            # For non-planner agents, send connection request
            if not self.is_planner:
                await self._send_connection_request()
            
        except Exception as e:
            logger.error(f"{self.agent_id} failed to start: {str(e)}")
            self.connection_state = ConnectionState.DISCONNECTED
            raise

    async def stop(self):
        """Stop the agent and clean up resources"""
        logger.info(f"Stopping {self.agent_id} agent...")
        self.running = False
        self.connection_state = ConnectionState.DISCONNECTED
        self.socket.close()
        self.context.term()
        logger.info(f"{self.agent_id} agent stopped")

    async def _send_connection_request(self):
        """Send connection request to planner"""
        try:
            connection_msg = MCPMessage(
                performative=MCPPerformatives.INFORM,
                content=json.dumps({
                    "type": "connect",
                    "agent_id": self.agent_id,
                    "status": "requesting_connection"
                }),
                sender=self.agent_id,
                receiver="planner"
            )
            await self.send_message(connection_msg)
            logger.info(f"{self.agent_id} sent connection request to planner")
        except Exception as e:
            logger.error(f"{self.agent_id} failed to send connection request: {str(e)}")
            self.connection_state = ConnectionState.DISCONNECTED

    async def send_message(self, message):
        """Send a message to another agent"""
        try:
            if not isinstance(message, MCPMessage):
                raise ValueError("Message must be an instance of MCPMessage")
            
            # Add protocol and timestamp if not present
            if not hasattr(message, 'protocol'):
                message.protocol = "MCP"
            if not hasattr(message, 'timestamp'):
                message.timestamp = datetime.now().isoformat()
            
            # Convert message to JSON
            message_json = message.to_json()
            
            if self.is_planner:
                # For planner, send to specific agent
                frames = [
                    message.receiver.encode(),  # recipient identity
                    b"",  # empty frame
                    message_json.encode()  # message content
                ]
            else:
                # For other agents, just send the message
                frames = [message_json.encode()]
            
            logger.info(f"{self.agent_id} sending message to {message.receiver}")
            await self.socket.send_multipart(frames)
            logger.info(f"{self.agent_id} message sent successfully")
            
        except Exception as e:
            logger.error(f"{self.agent_id} failed to send message: {str(e)}")
            raise

    async def _receive_messages(self):
        """Continuously receive and process messages"""
        logger.info(f"{self.agent_id} starting message receiver")
        while self.running:
            try:
                # Receive multipart message
                frames = await self.socket.recv_multipart()
                
                if self.is_planner:
                    if len(frames) < 3:
                        logger.error(f"{self.agent_id} received invalid message format")
                        continue
                    
                    sender_identity = frames[0].decode()
                    message_json = frames[2].decode()
                else:
                    message_json = frames[0].decode()
                    sender_identity = "planner"  # For non-planner agents, sender is always planner
                
                try:
                    message = MCPMessage.from_json(message_json)
                    logger.info(f"{self.agent_id} received message from {sender_identity}")
                    logger.debug(f"Message content: {message_json}")
                    
                    # Handle message
                    await self.handle_message(message)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"{self.agent_id} failed to parse message JSON: {str(e)}")
                    continue
                
            except zmq.error.ZMQError as e:
                if e.errno == zmq.EAGAIN:
                    continue
                logger.error(f"{self.agent_id} ZMQ error: {str(e)}")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"{self.agent_id} error processing message: {str(e)}")
                await asyncio.sleep(1)

    async def handle_message(self, message):
        """Handle incoming messages - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement handle_message")

    async def is_connected(self):
        """Check if the agent is connected"""
        return self.connection_state == ConnectionState.CONNECTED

    async def handle_connection_message(self, message):
        """Handle connection-related messages"""
        try:
            content = json.loads(message.content)
            msg_type = content.get("type")
            
            if msg_type == "connect":
                # Planner received connection request
                agent_id = content.get("agent_id")
                logger.info(f"{self.agent_id} received connection request from {agent_id}")
                
                # Send connection acknowledgment
                response = MCPMessage(
                    performative=MCPPerformatives.CONFIRM,
                    content=json.dumps({
                        "type": "connected",
                        "status": "connected",
                        "message": f"Connection established with {agent_id}"
                    }),
                    sender=self.agent_id,
                    receiver=agent_id
                )
                await self.send_message(response)
                self.connected_agents.add(agent_id)
                logger.info(f"{self.agent_id} connection established with {agent_id}")
                
            elif msg_type == "connected":
                # Agent received connection acknowledgment
                logger.info(f"{self.agent_id} received connection acknowledgment")
                self.connection_state = ConnectionState.CONNECTED
                logger.info(f"{self.agent_id} connection state: {self.connection_state.value}")
                
        except json.JSONDecodeError as e:
            logger.error(f"{self.agent_id} failed to parse connection message: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"{self.agent_id} error handling connection message: {str(e)}")
            return False
        
        return True