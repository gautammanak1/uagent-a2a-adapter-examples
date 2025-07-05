"""Writing agent using OpenAI for content creation and editing."""

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


class WritingAgentExecutor(AgentExecutor):
    """Writing agent that specializes in content creation and editing."""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"
        self.system_prompt = """
You are a Professional Writing Specialist AI agent. Your expertise includes:

1. Creative writing (stories, articles, blogs)
2. Technical writing (documentation, reports)
3. Business writing (emails, proposals, presentations)
4. Content editing and proofreading
5. Style adaptation for different audiences
6. SEO-optimized content creation

Writing Commands you can handle:
- WRITE:[type]:[topic] - Create new content
- EDIT:[text] - Edit and improve existing text
- SUMMARIZE:[text] - Create concise summaries
- REWRITE:[style]:[text] - Rewrite in different style
- PROOFREAD:[text] - Check grammar and style

Always provide high-quality, engaging, and well-structured content.
        """
    
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        message_content = ""
        for part in context.message.parts:
            if isinstance(part, Part) and isinstance(part.root, TextPart):
                message_content = part.root.text
                break
        
        try:
            # Parse command if it's a structured writing request
            if message_content.startswith("WRITE:"):
                await self._handle_write_command(message_content, event_queue)
            elif message_content.startswith("EDIT:"):
                await self._handle_edit_command(message_content, event_queue)
            elif message_content.startswith("SUMMARIZE:"):
                await self._handle_summarize_command(message_content, event_queue)
            elif message_content.startswith("REWRITE:"):
                await self._handle_rewrite_command(message_content, event_queue)
            elif message_content.startswith("PROOFREAD:"):
                await self._handle_proofread_command(message_content, event_queue)
            else:
                # General writing request
                await self._handle_general_request(message_content, event_queue)
                
        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Writing error: {str(e)}")
            )
    
    async def _handle_write_command(self, command: str, event_queue: EventQueue):
        """Handle WRITE:type:topic commands."""
        parts = command.split(":", 2)
        if len(parts) < 3:
            await event_queue.enqueue_event(
                new_agent_text_message("❌ Usage: WRITE:type:topic (e.g., WRITE:blog:AI trends)")
            )
            return
        
        content_type = parts[1]
        topic = parts[2]
        
        prompt = f"Write a {content_type} about: {topic}"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        
        formatted_response = f"""
✍️ Writing Agent - Content Creation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Type: {content_type.title()}
🎯 Topic: {topic}

{content}

✅ Content created by AI Writing Specialist
        """
        
        await event_queue.enqueue_event(new_agent_text_message(formatted_response))
    
    async def _handle_edit_command(self, command: str, event_queue: EventQueue):
        """Handle EDIT:text commands."""
        text_to_edit = command.replace("EDIT:", "", 1)
        
        prompt = f"Please edit and improve the following text for clarity, grammar, and style:\n\n{text_to_edit}"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        edited_content = response.choices[0].message.content
        
        formatted_response = f"""
✏️ Writing Agent - Text Editing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Original Text:
{text_to_edit[:200]}{'...' if len(text_to_edit) > 200 else ''}

✨ Edited Version:
{edited_content}

✅ Text edited by AI Writing Specialist
        """
        
        await event_queue.enqueue_event(new_agent_text_message(formatted_response))
    
    async def _handle_summarize_command(self, command: str, event_queue: EventQueue):
        """Handle SUMMARIZE:text commands."""
        text_to_summarize = command.replace("SUMMARIZE:", "", 1)
        
        prompt = f"Please create a concise summary of the following text:\n\n{text_to_summarize}"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content
        
        formatted_response = f"""
📄 Writing Agent - Text Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Summary:
{summary}

✅ Summary created by AI Writing Specialist
        """
        
        await event_queue.enqueue_event(new_agent_text_message(formatted_response))
    
    async def _handle_rewrite_command(self, command: str, event_queue: EventQueue):
        """Handle REWRITE:style:text commands."""
        parts = command.split(":", 2)
        if len(parts) < 3:
            await event_queue.enqueue_event(
                new_agent_text_message("❌ Usage: REWRITE:style:text (e.g., REWRITE:formal:casual text)")
            )
            return
        
        style = parts[1]
        text = parts[2]
        
        prompt = f"Please rewrite the following text in a {style} style:\n\n{text}"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.5
        )
        
        rewritten_text = response.choices[0].message.content
        
        formatted_response = f"""
🔄 Writing Agent - Style Rewrite
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎨 Target Style: {style.title()}

📝 Rewritten Text:
{rewritten_text}

✅ Text rewritten by AI Writing Specialist
        """
        
        await event_queue.enqueue_event(new_agent_text_message(formatted_response))
    
    async def _handle_proofread_command(self, command: str, event_queue: EventQueue):
        """Handle PROOFREAD:text commands."""
        text_to_proofread = command.replace("PROOFREAD:", "", 1)
        
        prompt = f"Please proofread the following text and identify any grammar, spelling, or style issues:\n\n{text_to_proofread}"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.2
        )
        
        proofread_result = response.choices[0].message.content
        
        formatted_response = f"""
🔍 Writing Agent - Proofreading
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Proofreading Results:
{proofread_result}

✅ Proofreading completed by AI Writing Specialist
        """
        
        await event_queue.enqueue_event(new_agent_text_message(formatted_response))
    
    async def _handle_general_request(self, message_content: str, event_queue: EventQueue):
        """Handle general writing requests."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Writing Request: {message_content}"}
            ],
            max_tokens=1500,
            temperature=0.6
        )
        
        content = response.choices[0].message.content
        
        formatted_response = f"""
✍️ Writing Agent Response
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Request: {message_content}

{content}

✅ Response by AI Writing Specialist
        """
        
        await event_queue.enqueue_event(new_agent_text_message(formatted_response))
    
    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(new_agent_text_message("Writing task cancelled."))
