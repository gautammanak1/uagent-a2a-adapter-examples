
import logging
from agents.travel_agent import TravelPlannerAgentExecutor
from agents.research_agent import ResearchAgentExecutor
from agents.coding_agent import CodingAgentExecutor
from utils.query_router import QueryRouter
from uagent_a2a_adapter import A2AAdapter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 Starting Multi-Agent System...")
    logger.info("📝 Available Agents:")
    logger.info("  - Travel Planner: Personalized travel itineraries")
    logger.info("  - Research Agent: Web and data research")
    logger.info("  - Coding Agent: Code generation and assistance")
    
    # Initialize agent executors
    travel_executor = TravelPlannerAgentExecutor()
    research_executor = ResearchAgentExecutor()
    coding_executor = CodingAgentExecutor()
    
    # Initialize query router
    router = QueryRouter(
        travel_executor=travel_executor,
        research_executor=research_executor,
        coding_executor=coding_executor
    )
    
    # Create single A2A adapter with one seed
    adapter = A2AAdapter(
        agent_executor=router,
        name="multi_agent_a2a",
        description="Multi-agent system with query routing",
        port=10001,
        a2a_port=9997,
        mailbox=True,
        seed="multi_agent_seed"
    )
    
    logger.info(f"🎯 Agent available at address: {adapter.uagent.address}")
    logger.info(f"🌐 A2A Server: http://localhost:9997")
    logger.info(f"🤖 uAgent Port: 10001")
    
    try:
        adapter.run()
    except KeyboardInterrupt:
        logger.info("👋 Shutting down Multi-Agent System...")
    except Exception as e:
        logger.error(f"Failed to start adapter: {str(e)}")
        raise

if __name__ == "__main__":
    main()