from .base_agent import BaseAgent
from config import MESSAGE_TYPES
from .message import Message
import logging
import json

logger = logging.getLogger(__name__)

class PlannerAgent(BaseAgent):
    def __init__(self, context, endpoint):
        super().__init__(context, endpoint)
        self.trip_requests = {}
        self.pending_responses = {}

    async def handle_message(self, message):
        """Handle incoming messages"""
        if message.msg_type == MESSAGE_TYPES["REQUEST"]:
            logger.info(f"Received trip request: {message.content}")
            
            # Parse trip request
            try:
                request_data = json.loads(message.content)
                trip_id = request_data.get("trip_id", "default")
                destination = request_data.get("destination", "Goa")
                dates = request_data.get("dates", {})
                
                # Store request details
                self.trip_requests[trip_id] = {
                    "destination": destination,
                    "dates": dates,
                    "status": "planning"
                }
                
                # Request travel options
                travel_msg = Message(
                    msg_type=MESSAGE_TYPES["REQUEST"],
                    content=json.dumps({
                        "trip_id": trip_id,
                        "destination": destination,
                        "dates": dates,
                        "type": "travel_options"
                    }),
                    sender="planner",
                    receiver="travel"
                )
                await self.send_message(travel_msg)
                
                # Request hotel options
                hotel_msg = Message(
                    msg_type=MESSAGE_TYPES["REQUEST"],
                    content=json.dumps({
                        "trip_id": trip_id,
                        "destination": destination,
                        "dates": dates,
                        "type": "hotel_options"
                    }),
                    sender="planner",
                    receiver="hotel"
                )
                await self.send_message(hotel_msg)
                
                # Acknowledge receipt to requester
                response = Message(
                    msg_type=MESSAGE_TYPES["RESPONSE"],
                    content=json.dumps({
                        "status": "planning_started",
                        "trip_id": trip_id,
                        "message": f"Planning your trip to {destination}"
                    }),
                    sender="planner",
                    receiver=message.sender
                )
                await self.send_message(response)
                
            except json.JSONDecodeError:
                logger.error("Invalid JSON in request")
                response = Message(
                    msg_type=MESSAGE_TYPES["RESPONSE"],
                    content="Invalid request format. Please provide valid JSON with trip details.",
                    sender="planner",
                    receiver=message.sender
                )
                await self.send_message(response)
                
        elif message.msg_type == MESSAGE_TYPES["RESPONSE"]:
            # Handle responses from travel and hotel agents
            try:
                response_data = json.loads(message.content)
                trip_id = response_data.get("trip_id")
                
                if trip_id in self.trip_requests:
                    if message.sender == "travel":
                        self.trip_requests[trip_id]["travel_options"] = response_data.get("options", [])
                    elif message.sender == "hotel":
                        self.trip_requests[trip_id]["hotel_options"] = response_data.get("options", [])
                    
                    # Check if we have both travel and hotel options
                    if "travel_options" in self.trip_requests[trip_id] and "hotel_options" in self.trip_requests[trip_id]:
                        # Create final trip plan
                        trip_plan = self._create_trip_plan(trip_id)
                        self.trip_requests[trip_id]["status"] = "completed"
                        
                        # Send final plan to requester
                        final_response = Message(
                            msg_type=MESSAGE_TYPES["INFORM"],
                            content=json.dumps(trip_plan),
                            sender="planner",
                            receiver=self.trip_requests[trip_id].get("requester", "travel")
                        )
                        await self.send_message(final_response)
                        
            except json.JSONDecodeError:
                logger.error("Invalid JSON in response")

    def _create_trip_plan(self, trip_id):
        """Create a comprehensive trip plan from available options"""
        request = self.trip_requests[trip_id]
        travel_options = request.get("travel_options", [])
        hotel_options = request.get("hotel_options", [])
        
        # Simple selection logic - can be made more sophisticated
        selected_travel = travel_options[0] if travel_options else {"status": "No travel options available"}
        selected_hotel = hotel_options[0] if hotel_options else {"status": "No hotel options available"}
        
        return {
            "trip_id": trip_id,
            "destination": request["destination"],
            "dates": request["dates"],
            "travel": selected_travel,
            "hotel": selected_hotel,
            "status": "planned"
        }