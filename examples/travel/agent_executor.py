from typing import override
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import TaskArtifactUpdateEvent, TaskStatus, TaskStatusUpdateEvent, TaskState
from a2a.utils import new_text_artifact
from travel.agent import TravelPlannerAgent
import logging

# Set up logging
logger = logging.getLogger(__name__)

class TravelPlannerAgentExecutor(AgentExecutor):
    """Travel Planner Agent Executor."""

    def __init__(self):
        self.agent = TravelPlannerAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        if not query or not context.message:
            logger.error("No valid query or message provided in context")
            raise Exception('No message or query provided')

        logger.info(f"Processing query: {query}")
        logger.info(f"Context ID: {context.context_id}, Task ID: {context.task_id}")

        try:
            full_response = ""  # Accumulate response for final artifact
            async for event in self.agent.stream(query):
                if not event.get('content') and not event.get('done'):
                    logger.warning("Empty event received from agent stream")
                    continue

                logger.debug(f"Streaming event: {event}")
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

            # Send final accumulated response as an artifact
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

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.warning("Cancel operation requested but not supported")
        raise Exception('Cancel not supported')