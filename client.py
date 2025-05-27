import asyncio
import zmq.asyncio
import json
import logging
import uuid
from agents.mcp_message import MCPMessage, MCPPerformatives
from config import AGENT_ENDPOINTS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TripPlanningClient:
    def __init__(self):
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.client_id = str(uuid.uuid4())  # Generate unique client ID
        self.socket.setsockopt_string(zmq.IDENTITY, self.client_id)  # Set client identity
        
        # Configure socket options
        self.socket.setsockopt(zmq.LINGER, 0)  # Don't wait on close
        self.socket.setsockopt(zmq.RCVTIMEO, -1)  # No timeout for receive
        self.socket.setsockopt(zmq.SNDTIMEO, 5000)  # 5 second timeout for send
        
        self.running = True
        logger.info(f"Client initialized with ID: {self.client_id}")

    async def connect(self):
        """Connect to the planner agent"""
        try:
            endpoint = AGENT_ENDPOINTS["planner"]
            logger.info(f"Connecting to planner agent at {endpoint}")
            
            # Try to connect
            self.socket.connect(endpoint)
            
            # Send a test message to check connection
            test_msg = MCPMessage(
                performative=MCPPerformatives.INFORM,
                content=json.dumps({
                    "type": "connection_test",
                    "status": "ready"
                }),
                sender=self.client_id,
                receiver="planner"
            )
            
            try:
                # For ROUTER socket, we need to send multipart message
                frames = [
                    b"",  # empty frame
                    test_msg.to_json().encode()  # message content
                ]
                await self.socket.send_multipart(frames)
                logger.info("Test message sent, waiting for response...")
                
                # Wait for response with timeout
                try:
                    # For ROUTER socket, we receive multipart message
                    frames = await asyncio.wait_for(self.socket.recv_multipart(), timeout=5.0)
                    if len(frames) >= 2:
                        response_json = frames[1].decode()
                        response = MCPMessage.from_json(response_json)
                        logger.info("Received response from planner agent")
                        return True
                    else:
                        logger.error("Invalid response format from planner agent")
                        return False
                except asyncio.TimeoutError:
                    logger.error("No response from planner agent. Is the server running?")
                    return False
                    
            except zmq.error.ZMQError as e:
                logger.error(f"Failed to send test message: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect: {str(e)}")
            return False

    async def send_trip_request(self, destination, check_in, check_out, budget="mid-range"):
        """Send a trip planning request to the planner agent"""
        trip_request = {
            "trip_id": f"TRIP-{check_in.replace('-', '')}",
            "destination": destination,
            "dates": {
                "check_in": check_in,
                "check_out": check_out
            },
            "preferences": {
                "budget": budget,
                "travel_type": "flexible"
            }
        }

        msg = MCPMessage(
            performative=MCPPerformatives.REQUEST,
            content=json.dumps(trip_request),
            sender=self.client_id,
            receiver="planner"
        )

        logger.info(f"Sending trip request for {destination}")
        try:
            # For ROUTER socket, we need to send multipart message
            frames = [
                b"",  # empty frame
                msg.to_json().encode()  # message content
            ]
            await self.socket.send_multipart(frames)
            logger.info("Trip request sent successfully")
        except Exception as e:
            logger.error(f"Failed to send trip request: {str(e)}")
            raise

    async def receive_responses(self):
        """Receive and process responses from the planner agent"""
        logger.info("Starting to receive responses...")
        while self.running:
            try:
                logger.debug("Waiting for message...")
                # For ROUTER socket, we receive multipart message
                frames = await self.socket.recv_multipart()
                if len(frames) >= 2:
                    message_json = frames[1].decode()
                    message = MCPMessage.from_json(message_json)
                    logger.info("Received message from planner")
                    logger.info(f"Message performative: {message.performative}")
                    
                    if message.performative == MCPPerformatives.INFORM:
                        # This is the final trip plan
                        plan = json.loads(message.content)
                        logger.info("\n=== Trip Plan ===")
                        logger.info(f"Destination: {plan['destination']}")
                        logger.info(f"Dates: {plan['dates']['check_in']} to {plan['dates']['check_out']}")
                        
                        # Display travel details
                        travel = plan['travel']
                        logger.info("\nTravel Details:")
                        if isinstance(travel, dict) and travel.get('status') != "No travel options available":
                            logger.info(f"Type: {travel['type']}")
                            if travel['type'] == 'flight':
                                logger.info(f"Airline: {travel['airline']}")
                            elif travel['type'] == 'train':
                                logger.info(f"Train: {travel['name']}")
                            elif travel['type'] == 'bus':
                                logger.info(f"Bus: {travel['name']}")
                            logger.info(f"Price: ₹{travel['price']}")
                            logger.info(f"Duration: {travel['duration']}")
                        else:
                            logger.info("No travel options available")
                        
                        # Display hotel details
                        hotel = plan['hotel']
                        logger.info("\nHotel Details:")
                        if isinstance(hotel, dict) and hotel.get('status') != "No hotel options available":
                            logger.info(f"Name: {hotel['name']}")
                            logger.info(f"Type: {hotel['type']}")
                            logger.info(f"Price per night: ₹{hotel['price_per_night']}")
                            logger.info(f"Amenities: {', '.join(hotel['amenities'])}")
                            logger.info(f"Rating: {hotel['rating']}/5.0")
                        else:
                            logger.info("No hotel options available")
                        
                        logger.info("\n=== End of Trip Plan ===\n")
                        
                    elif message.performative == MCPPerformatives.CONFIRM:
                        # This is a confirmation message
                        content = json.loads(message.content)
                        logger.info(f"Confirmation: {content['message']}")
                        
                    elif message.performative == MCPPerformatives.FAILURE:
                        # This is an error message
                        logger.error(f"Error: {message.content}")
                else:
                    logger.error("Invalid message format received")
                    
            except zmq.error.ZMQError as e:
                if e.errno == zmq.EAGAIN:
                    # This is a timeout, which is expected
                    continue
                logger.error(f"ZMQ error receiving message: {str(e)}")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error receiving message: {str(e)}")
                await asyncio.sleep(1)

    async def close(self):
        """Close the client connection"""
        logger.info("Closing client connection...")
        self.running = False
        self.socket.close()
        self.context.term()
        logger.info("Client connection closed")

async def main():
    client = TripPlanningClient()
    receiver_task = None
    
    try:
        # Connect to planner agent
        connected = await client.connect()
        if not connected:
            logger.error("Failed to connect to planner agent. Please make sure main.py is running.")
            return
        
        # Start the response receiver
        receiver_task = asyncio.create_task(client.receive_responses())
        
        # Send trip request
        await client.send_trip_request(
            destination="Goa",
            check_in="2024-04-01",
            check_out="2024-04-07",
            budget="mid-range"
        )
        
        # Wait for responses
        logger.info("Waiting for responses...")
        await asyncio.sleep(30)  # Wait longer to ensure we get all responses
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        await client.close()
        if receiver_task:
            receiver_task.cancel()
            try:
                await receiver_task
            except asyncio.CancelledError:
                pass

if __name__ == "__main__":
    asyncio.run(main()) 