"""Research agent using OpenAI for information gathering and analysis."""

import os
from typing import Dict, Any
from dotenv import load_dotenv

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Part, TextPart
from a2a.utils import new_agent_text_message
from typing_extensions import override

import openai

# Load environment variables
load_dotenv()


class ResearchAgentExecutor(AgentExecutor):
    """Research agent that specializes in information gathering and analysis."""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"
        self.system_prompt = """
You are a Research Specialist AI agent. Your role is to:

1. Conduct thorough research on any given topic
2. Provide well-structured, factual information
3. Cite sources when possible
4. Analyze trends and patterns
5. Summarize complex information clearly
6. Identify key insights and implications

Always structure your responses with:
- Executive Summary
- Key Findings
- Detailed Analysis
- Recommendations
- Sources/References (when applicable)

Be thorough, accurate, and professional in your research approach.
        """
    
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        message_content = ""
        for part in context.message.parts:
            if isinstance(part, Part) and isinstance(part.root, TextPart):
                message_content = part.root.text
                break
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Research Request: {message_content}"}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            research_result = response.choices[0].message.content
            
            # Format the response
            formatted_response = f"""
🔍 Research Agent Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Query: {message_content}

{research_result}

✅ Research completed by AI Research Specialist
            """
            
            await event_queue.enqueue_event(new_agent_text_message(formatted_response))
            
        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Research error: {str(e)}")
            )
    
    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(new_agent_text_message("Research cancelled."))
