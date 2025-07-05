from travel.agent_executor import TravelPlannerAgentExecutor
from uagent_a2a_adapter import A2AAdapter

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 Starting Travel Planner A2A Agent...")
    logger.info("📝 Features:")
    logger.info("  - Personalized travel itineraries")
    logger.info("  - Destination recommendations")
    logger.info("  - Practical travel tips")
    logger.info("  - Streaming responses")
    
    # Create a single agent executor instance
    agent_executor = TravelPlannerAgentExecutor()
    
    # Create A2A adapter with the shared executor
    adapter = A2AAdapter(
        agent_executor=agent_executor,
        name="travel_planner_a2a_agent",
        description="A travel planning agent with A2A capabilities",
        port=10001,
        a2a_port=9997,
        mailbox=True,
        seed="travel_planner_seed"
    )
    
    logger.info("Starting adapter...")
    logger.info(f"🎯 Agent will be available at address: {adapter.uagent.address}")
    logger.info(f"🌐 A2A Server: http://localhost:9997")
    logger.info(f"🤖 uAgent Port: 10001")
    
    try:
        adapter.run()
    except KeyboardInterrupt:
        logger.info("👋 Shutting down Travel Planner Agent...")
    except Exception as e:
        logger.error(f"Failed to start adapter: {str(e)}")
        raise

if __name__ == "__main__":
    main()
