# advanced_a2a_executor.py

import asyncio
from typing import Dict
from typing_extensions import override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Part, TextPart
from a2a.utils import new_agent_text_message
from agno.agent import Agent, Message, RunResponse
from agno.models.openai import OpenAIChat


class AdvancedAgentExecutor(AgentExecutor):
    """Advanced A2A Agent Executor with custom logic."""

    def __init__(self):
        self.agent = Agent(
            model=OpenAIChat(id="gpt-4o-mini"),
            instructions="""
            You are an advanced AI assistant with the following capabilities:
            1. Answer questions with detailed explanations
            2. Provide code examples when relevant
            3. Offer step-by-step solutions for complex problems
            4. Maintain context across conversations

            Always be helpful, accurate, and concise.
            """
        )
        self.conversation_history: Dict[str, list] = {}

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        message_content = ""

        for part in context.message.parts:
            if isinstance(part, Part) and isinstance(part.root, TextPart):
                message_content = part.root.text
                break

        message = Message(role="user", content=message_content)

        try:
            result: RunResponse = await self.agent.arun(message)
            await event_queue.enqueue_event(
                new_agent_text_message(result.content)
            )
        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"Error processing request: {str(e)}")
            )

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(
            new_agent_text_message("Task cancelled by user request.")
        )
