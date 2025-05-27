from .base_agent import BaseAgent
from .mcp_message import MCPMessage, MCPPerformatives
import logging
import json

logger = logging.getLogger(__name__)

class PlannerAgent(BaseAgent):
    def __init__(self, agent_id, endpoint, travel_agent_id="travel", hotel_agent_id="hotel"):
        super().__init__(agent_id, endpoint, is_planner=True)
        self.trip_requests = {}
        self.travel_agent_id = travel_agent_id
        self.hotel_agent_id = hotel_agent_id
        logger.info(f"PlannerAgent initialized with travel_agent_id={self.travel_agent_id}, hotel_agent_id={self.hotel_agent_id}")

    async def handle_message(self, message):
        """Handle incoming MCP messages"""
        logger.info(f"PlannerAgent received message: {message.performative} from {message.sender}")
        logger.info(f"Message content: {message.content}")
        
        try:
            content = json.loads(message.content)
            
            # Handle connection messages first
            if content.get("type") in ["connect", "connected"]:
                if await self.handle_connection_message(message):
                    return
            
            # Handle connection test
            if content.get("type") == "connection_test":
                logger.info("Received connection test, sending response")
                response = message.create_reply(
                    MCPPerformatives.CONFIRM,
                    json.dumps({"status": "connected", "message": "Planner agent is ready"})
                )
                await self.send_message(response)
                return
            
            if message.performative == MCPPerformatives.REQUEST:
                logger.info(f"Processing trip request from {message.sender}")
                
                trip_id = content.get("trip_id", "default")
                logger.info(f"Processing trip ID: {trip_id}")
                
                # Check if all required agents are connected
                if not await self.is_connected():
                    logger.error("Planner is not fully connected")
                    response = message.create_reply(
                        MCPPerformatives.FAILURE,
                        json.dumps({
                            "status": "error",
                            "message": "Planner is not fully connected"
                        })
                    )
                    await self.send_message(response)
                    return
                
                if self.travel_agent_id not in self.connected_agents:
                    logger.error(f"Travel agent {self.travel_agent_id} is not connected")
                    response = message.create_reply(
                        MCPPerformatives.FAILURE,
                        json.dumps({
                            "status": "error",
                            "message": "Travel agent is not connected"
                        })
                    )
                    await self.send_message(response)
                    return
                
                if self.hotel_agent_id not in self.connected_agents:
                    logger.error(f"Hotel agent {self.hotel_agent_id} is not connected")
                    response = message.create_reply(
                        MCPPerformatives.FAILURE,
                        json.dumps({
                            "status": "error",
                            "message": "Hotel agent is not connected"
                        })
                    )
                    await self.send_message(response)
                    return
                
                # Store request details
                self.trip_requests[trip_id] = {
                    "destination": content.get("destination", "Goa"),
                    "dates": content.get("dates", {}),
                    "status": "planning",
                    "requester": message.sender
                }
                logger.info(f"Stored request details for trip {trip_id}")
                
                # Call for proposals from travel agent
                travel_msg = MCPMessage(
                    performative=MCPPerformatives.CFP,
                    content=json.dumps({
                        "trip_id": trip_id,
                        "destination": content.get("destination", "Goa"),
                        "dates": content.get("dates", {}),
                        "type": "travel_options"
                    }),
                    sender=self.agent_id,
                    receiver=self.travel_agent_id
                )
                logger.info(f"Sending CFP to travel agent {self.travel_agent_id}")
                await self.send_message(travel_msg)
                logger.info("CFP sent to travel agent")
                
                # Call for proposals from hotel agent
                hotel_msg = MCPMessage(
                    performative=MCPPerformatives.CFP,
                    content=json.dumps({
                        "trip_id": trip_id,
                        "destination": content.get("destination", "Goa"),
                        "dates": content.get("dates", {}),
                        "type": "hotel_options"
                    }),
                    sender=self.agent_id,
                    receiver=self.hotel_agent_id
                )
                logger.info(f"Sending CFP to hotel agent {self.hotel_agent_id}")
                await self.send_message(hotel_msg)
                logger.info("CFP sent to hotel agent")
                
                # Acknowledge receipt
                response = message.create_reply(
                    MCPPerformatives.CONFIRM,
                    json.dumps({
                        "status": "planning_started",
                        "trip_id": trip_id,
                        "message": f"Planning your trip to {content.get('destination', 'Goa')}"
                    })
                )
                logger.info("Sending confirmation to requester")
                await self.send_message(response)
                logger.info("Confirmation sent to requester")
                
            elif message.performative == MCPPerformatives.PROPOSE:
                # Handle proposals from travel and hotel agents
                logger.info(f"Received proposal from {message.sender}")
                try:
                    proposal_data = json.loads(message.content)
                    trip_id = proposal_data.get("trip_id")
                    logger.info(f"Processing proposal for trip {trip_id}")
                    
                    if trip_id in self.trip_requests:
                        if message.sender == self.travel_agent_id:
                            logger.info("Storing travel options")
                            self.trip_requests[trip_id]["travel_options"] = proposal_data.get("options", [])
                        elif message.sender == self.hotel_agent_id:
                            logger.info("Storing hotel options")
                            self.trip_requests[trip_id]["hotel_options"] = proposal_data.get("options", [])
                        
                        # Check if we have both travel and hotel options
                        if "travel_options" in self.trip_requests[trip_id] and "hotel_options" in self.trip_requests[trip_id]:
                            logger.info("Both travel and hotel options received, creating trip plan")
                            # Create final trip plan
                            trip_plan = self._create_trip_plan(trip_id)
                            self.trip_requests[trip_id]["status"] = "completed"
                            
                            # Send final plan to requester
                            final_response = MCPMessage(
                                performative=MCPPerformatives.INFORM,
                                content=json.dumps(trip_plan),
                                sender=self.agent_id,
                                receiver=self.trip_requests[trip_id].get("requester")
                            )
                            logger.info("Sending final trip plan to requester")
                            await self.send_message(final_response)
                            logger.info("Final trip plan sent")
                            
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in proposal")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request")
            response = message.create_reply(
                MCPPerformatives.FAILURE,
                "Invalid request format. Please provide valid JSON with trip details."
            )
            await self.send_message(response)

    def _create_trip_plan(self, trip_id):
        """Create a comprehensive trip plan from available options"""
        logger.info(f"Creating trip plan for {trip_id}")
        request = self.trip_requests[trip_id]
        travel_options = request.get("travel_options", [])
        hotel_options = request.get("hotel_options", [])
        
        # Simple selection logic - can be made more sophisticated
        selected_travel = travel_options[0] if travel_options else {"status": "No travel options available"}
        selected_hotel = hotel_options[0] if hotel_options else {"status": "No hotel options available"}
        
        plan = {
            "trip_id": trip_id,
            "destination": request["destination"],
            "dates": request["dates"],
            "travel": selected_travel,
            "hotel": selected_hotel,
            "status": "planned"
        }
        logger.info(f"Trip plan created: {json.dumps(plan, indent=2)}")
        return plan