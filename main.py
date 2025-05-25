import asyncio
import zmq
import zmq.asyncio
from agents.planner_agent import PlannerAgent
from agents.travel_agent import TravelAgent
from agents.hotel_agent import HotelAgent
from config import AGENT_ENDPOINTS, MESSAGE_TYPES
from agents.message import Message
import logging
import json
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_agent(agent, name, max_retries=3):
    for attempt in range(max_retries):
        try:
            await agent.start()
            logger.info(f"{name} agent started successfully")
            return True
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed for {name} agent: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
            else:
                raise
    return False

async def main():
    agents = {}
    try:
        # Initialize ZMQ context
        context = zmq.asyncio.Context()

        logger.info("Initializing agents...")
        agents["planner"] = PlannerAgent(context, AGENT_ENDPOINTS["planner"])
        agents["travel"] = TravelAgent(context, AGENT_ENDPOINTS["travel"])
        agents["hotel"] = HotelAgent(context, AGENT_ENDPOINTS["hotel"])

        # Start agents with retry logic
        for name, agent in agents.items():
            await start_agent(agent, name)

        # Wait for agents to initialize
        await asyncio.sleep(2)

        # Create trip request
        tomorrow = datetime.now() + timedelta(days=1)
        next_week = tomorrow + timedelta(days=7)
        
        trip_request = {
            "trip_id": "TRIP001",
            "destination": "Goa",
            "dates": {
                "departure": tomorrow.strftime("%Y-%m-%d"),
                "return": next_week.strftime("%Y-%m-%d")
            },
            "preferences": {
                "budget": "mid-range",
                "travel_type": "flexible"
            }
        }

        # Send initial message
        msg = Message(
            msg_type=MESSAGE_TYPES["REQUEST"],
            content=json.dumps(trip_request),
            sender="travel",
            receiver="planner"
        )
        await agents["travel"].send_message(msg)
        logger.info("Trip request sent to planner")

        logger.info("System started. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise
    finally:
        # Cleanup
        logger.info("Stopping agents...")
        for name, agent in agents.items():
            try:
                await agent.stop()
                logger.info(f"{name} agent stopped")
            except Exception as e:
                logger.error(f"Error stopping {name} agent: {str(e)}")
        context.term()

if __name__ == "__main__":
    asyncio.run(main())