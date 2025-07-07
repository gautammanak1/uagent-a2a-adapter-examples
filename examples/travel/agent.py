import os
import json
import requests
from typing import Dict, Any
from dotenv import load_dotenv
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Part, TextPart
from a2a.utils import new_agent_text_message
from typing_extensions import override

# Load environment variables
load_dotenv()

class TripPlannerAgentExecutor(AgentExecutor):
    """Trip planner agent that specializes in creating and managing travel itineraries."""
    
    def __init__(self):
        self.url = "https://api.asi1.ai/v1/chat/completions"
        self.api_key = "sk_5822be6c948d4a25830382b308f6f51ee13629ffe6fc4dc7a064cc26e486df84"
        self.model = "asi1-mini"
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        self.system_prompt = """You are a Professional Trip Planner AI agent. Your expertise includes:
1. Creating detailed travel itineraries
2. Recommending destinations based on preferences
3. Suggesting activities, accommodations, and dining
4. Providing travel tips and logistics
5. Budget planning for trips
6. Customizing plans for different traveler types

Trip Planning Commands you can handle:
- PLAN:[destination]:[duration]:[preferences] - Create a travel itinerary
- RECOMMEND:[type]:[preferences] - Recommend destinations or activities
- BUDGET:[destination]:[amount] - Plan a trip within a budget
- TIPS:[destination] - Provide travel tips for a destination
- MODIFY:[itinerary] - Modify an existing itinerary

Always provide detailed, practical, and well-structured travel plans.
        """
    
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        message_content = ""
        for part in context.message.parts:
            if isinstance(part, Part) and isinstance(part.root, TextPart):
                message_content = part.root.text
                break
        
        try:
            # Parse command if it's a structured trip planning request
            if message_content.startswith("PLAN:"):
                await self._handle_plan_command(message_content, event_queue)
            elif message_content.startswith("RECOMMEND:"):
                await self._handle_recommend_command(message_content, event_queue)
            elif message_content.startswith("BUDGET:"):
                await self._handle_budget_command(message_content, event_queue)
            elif message_content.startswith("TIPS:"):
                await self._handle_tips_command(message_content, event_queue)
            elif message_content.startswith("MODIFY:"):
                await self._handle_modify_command(message_content, event_queue)
            else:
                # General trip planning request
                await self._handle_general_request(message_content, event_queue)
                
        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(f"❌ Trip planning error: {str(e)}")
            )
    
    async def _handle_plan_command(self, command: str, event_queue: EventQueue):
        """Handle PLAN:destination:duration:preferences commands."""
        parts = command.split(":", 3)
        if len(parts) < 3:
            await event_queue.enqueue_event(
                new_agent_text_message("❌ Usage: PLAN:destination:duration:preferences (e.g., PLAN:Paris:5 days:Family-friendly)")
            )
            return
        
        destination = parts[1]
        duration = parts[2]
        preferences = parts[3] if len(parts) > 3 else "general"
        
        prompt = f"Create a detailed travel itinerary for a {duration} trip to {destination} with preferences: {preferences}"
        
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.7,
            "stream": False
        })
        
        response = requests.post(self.url, headers=self.headers, data=payload)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        
        formatted_response = f"""🗺️ Trip Planner Agent - Itinerary Creation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Destination: {destination}
⏳ Duration: {duration}
🎯 Preferences: {preferences}

{content}

✅ Itinerary created by AI Trip Planner
        """
        
        await event_queue.enqueue_event(new_agent_text_message(formatted_response))
    
    async def _handle_recommend_command(self, command: str, event_queue: EventQueue):
        """Handle RECOMMEND:type:preferences commands."""
        parts = command.split(":", 2)
        if len(parts) < 2:
            await event_queue.enqueue_event(
                new_agent_text_message("❌ Usage: RECOMMEND:type:preferences (e.g., RECOMMEND:destinations:Adventure)")
            )
            return
        
        rec_type = parts[1]
        preferences = parts[2] if len(parts) > 2 else "general"
        
        prompt = f"Recommend {rec_type} for a trip with preferences: {preferences}"
        
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.6,
            "stream": False
        })
        
        response = requests.post(self.url, headers=self.headers, data=payload)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        
        formatted_response = f"""🌟 Trip Planner Agent - Recommendations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Type: {rec_type.title()}
🎯 Preferences: {preferences}

{content}

✅ Recommendations by AI Trip Planner
        """
        
        await event_queue.enqueue_event(new_agent_text_message(formatted_response))
    
    async def _handle_budget_command(self, command: str, event_queue: EventQueue):
        """Handle BUDGET:destination:amount commands."""
        parts = command.split(":", 2)
        if len(parts) < 3:
            await event_queue.enqueue_event(
                new_agent_text_message("❌ Usage: BUDGET:destination:amount (e.g., BUDGET:Bali:2000 USD)")
            )
            return
        
        destination = parts[1]
        amount = parts[2]
        
        prompt = f"Plan a trip to {destination} within a budget of {amount}"
        
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.6,
            "stream": False
        })
        
        response = requests.post(self.url, headers=self.headers, data=payload)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        
        formatted_response = f"""💰 Trip Planner Agent - Budget Planning
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Destination: {destination}
💵 Budget: {amount}

{content}

✅ Budget plan by AI Trip Planner
        """
        
        await event_queue.enqueue_event(new_agent_text_message(formatted_response))
    
    async def _handle_tips_command(self, command: str, event_queue: EventQueue):
        """Handle TIPS:destination commands."""
        destination = command.replace("TIPS:", "", 1)
        
        prompt = f"Provide travel tips for visiting {destination}"
        
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.6,
            "stream": False
        })
        
        response = requests.post(self.url, headers=self.headers, data=payload)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        
        formatted_response = f"""ℹ️ Trip Planner Agent - Travel Tips
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Destination: {destination}

{content}

✅ Tips by AI Trip Planner
        """
        
        await event_queue.enqueue_event(new_agent_text_message(formatted_response))
    
    async def _handle_modify_command(self, command: str, event_queue: EventQueue):
        """Handle MODIFY:itinerary commands."""
        itinerary = command.replace("MODIFY:", "", 1)
        
        prompt = f"Modify the following travel itinerary for improvements or updates:\n\n{itinerary}"
        
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.6,
            "stream": False
        })
        
        response = requests.post(self.url, headers=self.headers, data=payload)
        response.raise_for_status()
        modified_content = response.json()['choices'][0]['message']['content']
        
        formatted_response = f"""✨ Trip Planner Agent - Itinerary Modification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Original Itinerary:
{itinerary[:200]}{'...' if len(itinerary) > 200 else ''}

🔄 Modified Itinerary:
{modified_content}

✅ Itinerary modified by AI Trip Planner
        """
        
        await event_queue.enqueue_event(new_agent_text_message(formatted_response))
    
    async def _handle_general_request(self, message_content: str, event_queue: EventQueue):
        """Handle general trip planning requests."""
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Trip Planning Request: {message_content}"}
            ],
            "max_tokens": 1500,
            "temperature": 0.6,
            "stream": False
        })
        
        response = requests.post(self.url, headers=self.headers, data=payload)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        
        formatted_response = f"""🗺️ Trip Planner Agent Response
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Request: {message_content}

{content}

✅ Response by AI Trip Planner
        """
        
        await event_queue.enqueue_event(new_agent_text_message(formatted_response))
    
    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(new_agent_text_message("Trip planning task cancelled."))