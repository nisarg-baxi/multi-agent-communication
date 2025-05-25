from .base_agent import BaseAgent
from config import MESSAGE_TYPES
from .message import Message
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class HotelAgent(BaseAgent):
    def __init__(self, context, endpoint):
        super().__init__(context, endpoint)
        self.hotel_options = {
            "Goa": [
                {
                    "name": "Taj Exotica",
                    "type": "luxury",
                    "price_per_night": 15000,
                    "amenities": ["pool", "spa", "beach_access"],
                    "rating": 4.8
                },
                {
                    "name": "Holiday Inn",
                    "type": "mid-range",
                    "price_per_night": 8000,
                    "amenities": ["pool", "restaurant"],
                    "rating": 4.2
                }
            ],
            "Mumbai": [
                {
                    "name": "Taj Mahal Palace",
                    "type": "luxury",
                    "price_per_night": 20000,
                    "amenities": ["pool", "spa", "multiple_restaurants"],
                    "rating": 4.9
                }
            ]
        }

    async def handle_message(self, message):
        """Handle incoming messages"""
        if message.msg_type == MESSAGE_TYPES["REQUEST"]:
            try:
                request_data = json.loads(message.content)
                trip_id = request_data.get("trip_id")
                destination = request_data.get("destination", "Goa")
                dates = request_data.get("dates", {})
                
                logger.info(f"Processing hotel request for {destination}")
                
                # Get hotel options for the destination
                options = self._get_hotel_options(destination, dates)
                
                # Send response back to planner
                response = Message(
                    msg_type=MESSAGE_TYPES["RESPONSE"],
                    content=json.dumps({
                        "trip_id": trip_id,
                        "options": options,
                        "status": "success"
                    }),
                    sender="hotel",
                    receiver=message.sender
                )
                await self.send_message(response)
                
            except json.JSONDecodeError:
                logger.error("Invalid JSON in request")
                response = Message(
                    msg_type=MESSAGE_TYPES["RESPONSE"],
                    content=json.dumps({
                        "status": "error",
                        "message": "Invalid request format"
                    }),
                    sender="hotel",
                    receiver=message.sender
                )
                await self.send_message(response)

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