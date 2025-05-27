from .base_agent import BaseAgent
from .mcp_message import MCPMessage, MCPPerformatives
import logging
import json
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class HotelAgent(BaseAgent):
    def __init__(self, agent_id, endpoint):
        super().__init__(agent_id, endpoint)
        self.hotel_options = {
            "Goa": [
                {
                    "name": "Taj Exotica",
                    "type": "luxury",
                    "price_per_night": 15000,
                    "amenities": ["pool", "spa", "beach access", "restaurant"],
                    "rating": 4.8
                },
                {
                    "name": "Holiday Inn",
                    "type": "mid-range",
                    "price_per_night": 8000,
                    "amenities": ["pool", "restaurant", "gym"],
                    "rating": 4.2
                }
            ],
            "Mumbai": [
                {
                    "name": "Taj Mahal Palace",
                    "type": "luxury",
                    "price_per_night": 20000,
                    "amenities": ["pool", "spa", "multiple restaurants", "gym"],
                    "rating": 4.9
                },
                {
                    "name": "ITC Maratha",
                    "type": "luxury",
                    "price_per_night": 18000,
                    "amenities": ["pool", "spa", "restaurant", "business center"],
                    "rating": 4.7
                }
            ]
        }
        logger.info("HotelAgent initialized")

    async def start(self):
        """Start the agent and notify the planner"""
        await super().start()
        logger.info("Hotel Agent : Starting")
        # Perform handshake with planner
        await self.perform_handshake("planner")
        logger.info("Hotel Agent : Handshake initiated with planner")

    async def handle_message(self, message):
        """Handle incoming MCP messages"""
        logger.info(f"HotelAgent received message: {message.performative} from {message.sender}")
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
                
                logger.info(f"Processing hotel request for {destination}")
                
                # Get hotel options for the destination
                options = self._get_hotel_options(destination, dates)
                
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
                
                logger.info("Sending hotel options")
                await self.send_message(response)
                logger.info("Hotel options sent")
                
            elif message.performative == MCPPerformatives.ACCEPT_PROPOSAL:
                trip_id = content.get("trip_id")
                selected_option = content.get("selected_option")
                
                # Confirm the booking
                response = MCPMessage(
                    performative=MCPPerformatives.CONFIRM,
                    content=json.dumps({
                        "trip_id": trip_id,
                        "status": "booked",
                        "booking_id": f"HOTEL-{random.randint(1000, 9999)}",
                        "selected_option": selected_option,
                        "message": "Hotel booking confirmed"
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

    def _calculate_nights(self, dates):
        """Calculate number of nights from check-in to check-out"""
        try:
            check_in = dates.get("check_in")
            check_out = dates.get("check_out")
            if check_in and check_out:
                check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
                check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
                return (check_out_date - check_in_date).days
        except (ValueError, TypeError):
            pass
        return 1  # Default to 1 night if dates are invalid

    def _get_hotel_options(self, destination, dates):
        """Get hotel options for the given destination and dates"""
        options = self.hotel_options.get(destination, [])
        
        # If no specific options for destination, return default options
        if not options:
            return [{
                "name": "Default Hotel",
                "type": "standard",
                "price_per_night": 5000,
                "amenities": ["basic"],
                "rating": 3.5,
                "note": "Generic option for unspecified destination"
            }]
        
        # Add date information and calculate total price
        for option in options:
            if dates:
                option["dates"] = dates
                # Calculate number of nights
                if "departure" in dates and "return" in dates:
                    start = datetime.strptime(dates["departure"], "%Y-%m-%d")
                    end = datetime.strptime(dates["return"], "%Y-%m-%d")
                    nights = (end - start).days
                    option["total_price"] = option["price_per_night"] * nights
            else:
                # Default to 7 nights if no dates provided
                tomorrow = datetime.now() + timedelta(days=1)
                option["dates"] = {
                    "check_in": tomorrow.strftime("%Y-%m-%d"),
                    "check_out": (tomorrow + timedelta(days=7)).strftime("%Y-%m-%d")
                }
                option["total_price"] = option["price_per_night"] * 7
        
        return options