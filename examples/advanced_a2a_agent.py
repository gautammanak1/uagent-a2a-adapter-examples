"""Advanced example with custom A2A agent executor."""

import os
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Part, TextPart
from a2a.utils import new_agent_text_message
from agno.agent import Agent, Message, RunResponse
from agno.models.openai import OpenAIChat
from typing_extensions import override

from uagents_adapter import A2AAdapter

# Load environment variables
load_dotenv()


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
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        message_content = ""
        
        # Extract message content
        for part in context.message.parts:
            if isinstance(part, Part):
                if isinstance(part.root, TextPart):
                    message_content = part.root.text
                    break
        
        # Create message with context
        message = Message(role="user", content=message_content)
        
        try:
            # Run the agent
            result: RunResponse = await self.agent.arun(message)
            
            # Send response
            await event_queue.enqueue_event(
                new_agent_text_message(result.content)
            )
            
        except Exception as e:
            error_message = f"Error processing request: {str(e)}"
            await event_queue.enqueue_event(
                new_agent_text_message(error_message)
            )

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(
            new_agent_text_message("Task cancelled by user request.")
        )


async def main():
    """Main function to run the advanced A2A agent."""
    
    # Create the agent executor
    executor = AdvancedAgentExecutor()
    
    # Create A2A adapter with custom configuration
    adapter = A2AAdapter(
        agent_executor=executor,
        name="advanced_a2a_agent",
        description="An advanced A2A agent with enhanced capabilities",
        port=8082,
        a2a_port=9997,
        mailbox=True,
        seed="advanced_agent_seed"
    )
    
    print("🚀 Starting Advanced A2A Agent...")
    print("📝 Features:")
    print("  - Detailed explanations")
    print("  - Code examples")
    print("  - Step-by-step solutions")
    print("  - Context awareness")
    print()
    
    # Run the adapter
    adapter.run()


if __name__ == "__main__":
    asyncio.run(main())
