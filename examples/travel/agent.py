import json
import os
import sys
from collections.abc import AsyncGenerator
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class TravelPlannerAgent:
    """Travel Planner Agent."""

    def __init__(self):
        """Initialize the travel dialogue model."""
        try:
            # Adjust path to config.json (relative to agent.py)
            config_path = os.path.join(os.path.dirname(__file__), '../config.json')
            with open(config_path) as f:
                config = json.load(f)
            api_key_name = config.get('api_key', 'OPENAI_API_KEY')
            api_key = os.getenv(api_key_name)
            if not api_key:
                logger.error(f'{api_key_name} environment variable not set.')
                sys.exit(1)

            self.model = ChatOpenAI(
                model=config.get('model_name', 'gpt-4o-mini'),
                base_url=config.get('base_url'),
                api_key=api_key,
                temperature=0.7,
                streaming=True  # Explicitly enable streaming
            )
            logger.info("TravelPlannerAgent initialized successfully")
        except FileNotFoundError:
            logger.error('Error: The configuration file config.json cannot be found.')
            sys.exit(1)
        except KeyError as e:
            logger.error(f'The configuration file is missing required fields: {e}')
            sys.exit(1)

    async def stream(self, query: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stream the response of the large model back to the client."""
        if not query:
            logger.error("Empty query received")
            yield {
                'content': 'Error: No query provided.',
                'done': True,
            }
            return

        logger.info(f"Streaming response for query: {query}")
        try:
            messages = [
                SystemMessage(
                    content="""
                    You are an expert travel assistant specializing in trip planning, destination information, 
                    and travel recommendations. Your goal is to help users plan enjoyable, safe, and 
                    realistic trips based on their preferences and constraints.
                    
                    When providing information:
                    - Be specific and practical with your advice
                    - Consider seasonality, budget constraints, and travel logistics
                    - Highlight cultural experiences and authentic local activities
                    - Include practical travel tips relevant to the destination
                    - Format information clearly with headings and bullet points when appropriate
                    
                    For itineraries:
                    - Create realistic day-by-day plans that account for travel time between attractions
                    - Balance popular tourist sites with off-the-beaten-path experiences
                    - Include approximate timing and practical logistics
                    - Suggest meal options highlighting local cuisine
                    - Consider weather, local events, and opening hours in your planning
                    
                    Always maintain a helpful, enthusiastic but realistic tone and acknowledge 
                    any limitations in your knowledge when appropriate.
                    """
                ),
                HumanMessage(content=query)
            ]

            accumulated_content = ""  # Accumulate content for debugging
            async for chunk in self.model.astream(messages):
                content = getattr(chunk, 'content', None)
                if content:
                    accumulated_content += content
                    logger.debug(f"Yielding chunk: {content}")
                    yield {'content': content, 'done': False}
                else:
                    logger.warning("Received empty or invalid chunk from model")
            logger.info(f"Full response accumulated: {accumulated_content}")
            yield {'content': '', 'done': True}
            logger.info("Streaming completed for query")

        except Exception as e:
            logger.error(f'Error during streaming: {str(e)}')
            yield {
                'content': f'Sorry, an error occurred while processing your request: {str(e)}',
                'done': True,
            }