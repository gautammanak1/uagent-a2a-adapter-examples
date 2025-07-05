"""Example of using A2ARegisterTool to register an A2A agent."""

import os
from dotenv import load_dotenv

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Part, TextPart
from a2a.utils import new_agent_text_message
from agno.agent import Agent, Message, RunResponse
from agno.models.openai import OpenAIChat
from typing_extensions import override

from uagents_adapter import A2ARegisterTool

# Load environment variables
load_dotenv()


class ResearchAgentExecutor(AgentExecutor):
    """Research A2A Agent Executor."""
    
    def __init__(self):
        self.agent = Agent(
            model=OpenAIChat(id="gpt-4o-mini"),
            instructions="You are a research assistant. Provide detailed, well-researched responses."
        )

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
    executor = ResearchAgentExecutor()
    
    # Create A2A register tool
    register_tool = A2ARegisterTool()
    
    # Register the agent as a uAgent
    result = register_tool.invoke({
        "agent_executor": executor,
        "name": "research_a2a_agent",
        "port": 8081,
        "a2a_port": 9998,
        "description": "A research assistant A2A agent",
        "mailbox": True,
        "api_token": os.getenv("AGENTVERSE_API_TOKEN"),  # Optional
        "return_dict": True
    })
    
    print(f"Created uAgent '{result['agent_name']}' with address {result['agent_address']}")
    print(f"uAgent port: {result['agent_port']}")
    print(f"A2A server port: {result['a2a_port']}")
    print(f"Mailbox enabled: {result['mailbox_enabled']}")
