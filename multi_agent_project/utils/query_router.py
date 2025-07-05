import logging
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import TaskArtifactUpdateEvent, TaskStatus, TaskStatusUpdateEvent, TaskState
from a2a.utils import new_text_artifact

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryRouter(AgentExecutor):
    """Routes queries to appropriate agent based on keywords."""
    
    def __init__(self, travel_executor, research_executor, coding_executor):
        self.travel_executor = travel_executor
        self.research_executor = research_executor
        self.coding_executor = coding_executor
        self.keyword_map = {
            'travel': self.travel_executor,
            'trip': self.travel_executor,
            'itinerary': self.travel_executor,
            'destination': self.travel_executor,
            'vacation': self.travel_executor,
            'research': self.research_executor,
            'find': self.research_executor,
            'information': self.research_executor,
            'data': self.research_executor,
            'analyze': self.research_executor,
            'code': self.coding_executor,
            'program': self.coding_executor,
            'script': self.coding_executor,
            'develop': self.coding_executor,
            'python': self.coding_executor
        }
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        if not query or not context.message:
            logger.error("No valid query or message provided")
            error_message = TaskArtifactUpdateEvent(
                contextId=context.context_id,
                taskId=context.task_id,
                artifact=new_text_artifact(
                    name='error',
                    text="No valid query or message provided"
                )
            )
            await event_queue.enqueue_event(error_message)
            status = TaskStatusUpdateEvent(
                contextId=context.context_id,
                taskId=context.task_id,
                status=TaskStatus(state=TaskState.failed),
                final=True
            )
            await event_queue.enqueue_event(status)
            return

        logger.info(f"Routing query: {query}")
        
        # Determine which agent to route to based on keywords
        query_lower = query.lower()
        selected_executor = None
        for keyword, executor in self.keyword_map.items():
            if keyword in query_lower:
                selected_executor = executor
                break
        
        # Default to travel executor if no keywords match
        if not selected_executor:
            logger.info("No specific keywords matched, defaulting to Travel Agent")
            selected_executor = self.travel_executor
        
        logger.info(f"Routing to {selected_executor.__class__.__name__}")
        
        try:
            await selected_executor.execute(context, event_queue)
        except Exception as e:
            logger.error(f"Error during execution: {str(e)}")
            error_message = TaskArtifactUpdateEvent(
                contextId=context.context_id,
                taskId=context.task_id,
                artifact=new_text_artifact(
                    name='error',
                    text=f"An error occurred: {str(e)}"
                )
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