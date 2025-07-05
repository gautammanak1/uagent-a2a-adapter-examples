"""Example of using A2A adapter with a basic agent."""

import os
from typing import List
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

# Create the Agno agent
agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
)


class BasicAgentExecutor(AgentExecutor):
    """Basic A2A Agent Executor using Agno."""
    
    def __init__(self):
        self.agent = agent

    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        message: Message = Message(role="user", content="")
        
        for part in context.message.parts:
            if isinstance(part, Part):
                if isinstance(part.root, TextPart):
                    message.content = part.root.text
                    break

        result: RunResponse = await self.agent.arun(message)
        await event_queue.enqueue_event(new_agent_text_message(result.content))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("Cancel not supported")


if __name__ == "__main__":
    # Create the agent executor
    executor = BasicAgentExecutor()
    
    # Create A2A adapter
    adapter = A2AAdapter(
        agent_executor=executor,
        name="basic_a2a_agent",
        description="A basic A2A agent using Agno and OpenAI",
        port=8080,
        a2a_port=9999,
        mailbox=True
    )
    
    # Run the adapter (this will start both A2A server and uAgent)
    adapter.run()
