from .base_agent import BaseAgent
from config import MESSAGE_TYPES
from .message import Message
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TravelAgent(BaseAgent):
    def __init__(self, context, endpoint):
        super().__init__(context, endpoint)
        self.travel_options = {
            "Goa": [
                {
                    "type": "flight",
                    "airline": "Air India",
                    "departure": "10:00",
                    "arrival": "12:00",
                    "price": 5000,
                    "class": "economy"
                },
                {
                    "type": "train",
                    "train_name": "Goa Express",
                    "departure": "18:00",
                    "arrival": "08:00",
                    "price": 1500,
                    "class": "sleeper"
                }
            ],
            "Mumbai": [
                {
                    "type": "flight",
                    "airline": "IndiGo",
                    "departure": "09:00",
                    "arrival": "11:00",
                    "price": 4000,
                    "class": "economy"
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
                
                logger.info(f"Processing travel request for {destination}")
                
                # Get travel options for the destination
                options = self._get_travel_options(destination, dates)
                
                # Send response back to planner
                response = Message(
                    msg_type=MESSAGE_TYPES["RESPONSE"],
                    content=json.dumps({
                        "trip_id": trip_id,
                        "options": options,
                        "status": "success"
                    }),
                    sender="travel",
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
                    sender="travel",
                    receiver=message.sender
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