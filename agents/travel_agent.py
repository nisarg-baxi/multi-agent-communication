from .base_agent import BaseAgent
from .mcp_message import MCPMessage, MCPPerformatives
import logging
import json
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TravelAgent(BaseAgent):
    def __init__(self, agent_id, endpoint):
        super().__init__(agent_id, endpoint)
        self.travel_options = {
            "Goa": [
                {
                    "type": "flight",
                    "airline": "Air India",
                    "price": 5000,
                    "duration": "2h 30m"
                },
                {
                    "type": "train",
                    "name": "Goa Express",
                    "price": 2000,
                    "duration": "12h"
                }
            ],
            "Mumbai": [
                {
                    "type": "flight",
                    "airline": "IndiGo",
                    "price": 4000,
                    "duration": "2h"
                },
                {
                    "type": "train",
                    "name": "Rajdhani Express",
                    "price": 1500,
                    "duration": "8h"
                }
            ]
        }
        logger.info("TravelAgent initialized")

    async def start(self):
        """Start the agent and notify the planner"""
        await super().start()
        logger.info("Travel Agent : Starting")
        # Perform handshake with planner
        await self.perform_handshake("planner")
        logger.info("Travel Agent : Handshake initiated with planner")

    async def handle_message(self, message):
        """Handle incoming MCP messages"""
        logger.info(f"TravelAgent received message: {message.performative} from {message.sender}")
        logger.info(f"Message content: {message.content}")
        
        try:
            content = json.loads(message.content)
            
            # Handle connection messages first
            if content.get("type") in ["connect", "connected"]:
                if await self.handle_connection_message(message):
                    return
                
            if message.performative == MCPPerformatives.CFP:
                trip_id = content.get("trip_id")
                destination = content.get("destination")
                dates = content.get("dates", {})
                
                logger.info(f"Processing travel request for {destination}")
                
                # Get travel options for the destination
                options = self._get_travel_options(destination, dates)
                
                # Create response
                response = MCPMessage(
                    performative=MCPPerformatives.PROPOSE,
                    content=json.dumps({
                        "trip_id": trip_id,
                        "options": options
                    }),
                    sender=self.agent_id,
                    receiver=message.sender
                )
                
                logger.info("Sending travel options")
                await self.send_message(response)
                logger.info("Travel options sent")
                
            elif message.performative == MCPPerformatives.ACCEPT_PROPOSAL:
                trip_id = content.get("trip_id")
                selected_option = content.get("selected_option")
                
                # Confirm the booking
                response = MCPMessage(
                    performative=MCPPerformatives.CONFIRM,
                    content=json.dumps({
                        "trip_id": trip_id,
                        "status": "booked",
                        "booking_id": f"TRAVEL-{random.randint(1000, 9999)}",
                        "selected_option": selected_option,
                        "message": "Travel booking confirmed"
                    }),
                    sender=self.agent_id,
                    receiver=message.sender
                )
                await self.send_message(response)
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON in message content")
            response = message.create_reply(
                MCPPerformatives.FAILURE,
                "Invalid message format"
            )
            await self.send_message(response)

    def _get_travel_options(self, destination, dates):
        """Get travel options for the given destination and dates"""
        options = self.travel_options.get(destination, [])
        
        # If no specific options for destination, return default options
        if not options:
            return [{
                "type": "flight",
                "airline": "Default Airlines",
                "departure": "09:00",
                "arrival": "11:00",
                "price": 4000,
                "class": "economy",
                "note": "Generic option for unspecified destination"
            }]
        
        # Add date information to options
        for option in options:
            if dates:
                option["dates"] = dates
            else:
                # Default to next day if no dates provided
                tomorrow = datetime.now() + timedelta(days=1)
                option["dates"] = {
                    "departure": tomorrow.strftime("%Y-%m-%d"),
                    "return": (tomorrow + timedelta(days=7)).strftime("%Y-%m-%d")
                }
        
        return options