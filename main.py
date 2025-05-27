import asyncio
import logging
from agents.planner_agent import PlannerAgent
from agents.travel_agent import TravelAgent
from agents.hotel_agent import HotelAgent
from config import AGENT_ENDPOINTS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Initialize planner first
        planner = PlannerAgent(
            "planner", 
            AGENT_ENDPOINTS["planner"],
            travel_agent_id="travel",
            hotel_agent_id="hotel"
        )
        
        # Initialize travel and hotel agents to connect to planner
        travel = TravelAgent("travel", AGENT_ENDPOINTS["planner"])
        hotel = HotelAgent("hotel", AGENT_ENDPOINTS["planner"])
        
        # Start planner first and wait for it to be ready
        logger.info("Starting planner agent...")
        await planner.start()
        logger.info("Planner agent started")
        await asyncio.sleep(1)  # Give planner time to bind
        
        # Start travel agent
        logger.info("Starting travel agent...")
        await travel.start()
        logger.info("Travel agent started")
        await asyncio.sleep(1)  # Give travel agent time to connect
        
        # Start hotel agent
        logger.info("Starting hotel agent...")
        await hotel.start()
        logger.info("Hotel agent started")
        await asyncio.sleep(1)  # Give hotel agent time to connect

        logger.info("All agents started successfully")
        
        # Keep the main process running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        # Stop agents in reverse order
        logger.info("Stopping agents...")
        await hotel.stop()
        await travel.stop()
        await planner.stop()
        logger.info("All agents stopped")

if __name__ == "__main__":
    asyncio.run(main())