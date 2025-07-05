import json
import os
import sys
import logging
from collections.abc import AsyncGenerator
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import TaskArtifactUpdateEvent, TaskStatus, TaskStatusUpdateEvent, TaskState
from a2a.utils import new_text_artifact

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class CodingAgent:
    """Coding Agent for code generation and assistance."""

    def __init__(self):
        try:
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
                streaming=True
            )
            logger.info("CodingAgent initialized successfully")
        except FileNotFoundError:
            logger.error('Error: config.json cannot be found.')
            sys.exit(1)
        except KeyError as e:
            logger.error(f'Config file missing required fields: {e}')
            sys.exit(1)

    async def stream(self, query: str) -> AsyncGenerator[dict[str, Any], None]:
        if not query:
            logger.error("Empty query received")
            yield {'content': 'Error: No query provided.', 'done': True}
            return

        logger.info(f"Streaming response for coding query: {query}")
        try:
            messages = [
                SystemMessage(
                    content="""
                    You are an expert coding assistant specializing in generating clean, efficient, 
                    and well-documented code. Your goal is to provide accurate code solutions 
                    based on user requirements.

                    When providing code:
                    - Include clear comments explaining the code
                    - Use proper formatting and follow language-specific style guides
                    - Provide complete, working code examples
                    - Handle edge cases and include error handling
                    - Suggest best practices for the requested programming language
                    - Include example usage when appropriate
                    """
                ),
                HumanMessage(content=query)
            ]

            accumulated_content = ""
            async for chunk in self.model.astream(messages):
                content = getattr(chunk, 'content', None)
                if content:
                    accumulated_content += content
                    logger.debug(f"Yielding chunk: {content}")
                    yield {'content': content, 'done': False}
                else:
                    logger.warning("Received empty or invalid chunk")
            logger.info(f"Full response: {accumulated_content}")
            yield {'content': '', 'done': True}
            logger.info("Streaming completed for query")

        except Exception as e:
            logger.error(f'Error during streaming: {str(e)}')
            yield {'content': f'Sorry, an error occurred: {str(e)}', 'done': True}

class CodingAgentExecutor(AgentExecutor):
    """Coding Agent Executor."""

    def __init__(self):
        self.agent = CodingAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        if not query or not context.message:
            logger.error("No valid query or message provided")
            raise Exception('No message or query provided')

        logger.info(f"Processing coding query: {query}")
        try:
            full_response = ""
            async for event in self.agent.stream(query):
                if not event.get('content') and not event.get('done'):
                    logger.warning("Empty event received")
                    continue

                full_response += event['content']
                message = TaskArtifactUpdateEvent(
                    contextId=context.context_id,
                    taskId=context.task_id,
                    artifact=new_text_artifact(
                        name='current_result',
                        text=event['content'],
                    ),
                )
                await event_queue.enqueue_event(message)
                if event['done']:
                    logger.info("Streaming completed")
                    break

            if full_response:
                final_message = TaskArtifactUpdateEvent(
                    contextId=context.context_id,
                    taskId=context.task_id,
                    artifact=new_text_artifact(
                        name='final_result',
                        text=full_response,
                    ),
                )
                await event_queue.enqueue_event(final_message)
                logger.info("Sent final accumulated response")

            status = TaskStatusUpdateEvent(
                contextId=context.context_id,
                taskId=context.task_id,
                status=TaskStatus(state=TaskState.completed),
                final=True
            )
            await event_queue.enqueue_event(status)
            logger.info("Task status updated to completed")

        except Exception as e:
            logger.error(f"Error during execution: {str(e)}")
            error_message = TaskArtifactUpdateEvent(
                contextId=context.context_id,
                taskId=context.task_id,
                artifact=new_text_artifact(
                    name='error',
                    text=f"An error occurred: {str(e)}",
                ),
            )
            await event_queue.enqueue_event(error_message)
            status = TaskStatusUpdateEvent(
                contextId=context.context_id,
                taskId=context.task_id,
                status=TaskStatus(state=TaskState.failed),
                final=True
            )
            await event_queue.enqueue_event(status)
            raise

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.warning("Cancel operation requested but not supported")
        raise Exception('Cancel not supported')