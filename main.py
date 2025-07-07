import asyncio
import threading
import time
from typing import Dict, List
from dataclasses import dataclass
from uagent_a2a_adapter import  A2AAdapter, A2AAgentConfig
from examples.travel.agent import TripPlannerAgentExecutor


@dataclass
class OpenAIAgentConfig:
    """Configuration for an OpenAI-powered agent."""
    name: str
    description: str
    port: int
    a2a_port: int
    specialties: List[str]
    executor_class: str

class OpenAIMultiAgentOrchestrator:
    """Orchestrator for multiple OpenAI-powered agents using the new multi-agent adapter."""
    
    def __init__(self):
        self.coordinator: A2AAdapter = None
        self.agent_configs: List[OpenAIAgentConfig] = []
        self.executors: Dict[str, any] = {}
        self.running = False

    def setup_agents(self):
        """Setup all OpenAI-powered agents with their configurations."""
        print("🔧 Setting up OpenAI Multi-Agent System")
        print("=" * 60)

        # Define OpenAI agent configurations
        self.agent_configs = [
    OpenAIAgentConfig(
        name="trip_planner",
        description="AI Trip Planner powered by OpenAI GPT-4 for creating travel itineraries, recommending destinations, and providing travel tips",
        port=8100,
        a2a_port=10020,
        specialties=["trip planning", "itinerary creation", "destination recommendations", "travel tips", "budget planning"],
        executor_class="TripPlannerAgentExecutor"
    ),
]
        self.executors = {
            "TripPlannerAgentExecutor": TripPlannerAgentExecutor(),
        }

        print("✅ Agent configurations created:")
        for config in self.agent_configs:
            print(f"   • {config.name}: {', '.join(config.specialties)}")

    def start_individual_a2a_servers(self):
        """Start individual A2A servers for each OpenAI agent."""
        from a2a.server.apps import A2AStarletteApplication
        from a2a.server.request_handlers import DefaultRequestHandler
        from a2a.server.tasks import InMemoryTaskStore
        from a2a.types import AgentCapabilities, AgentCard, AgentSkill
        import uvicorn

        def start_server(config: OpenAIAgentConfig, executor):
            """Start an individual A2A server for an agent."""
            try:
                # Create A2A server components
                skill = AgentSkill(
                    id=f"{config.name.lower()}_skill",
                    name=config.name.replace("_", " ").title(),
                    description=config.description,
                    tags=config.specialties,
                    examples=[f"Help with {specialty.lower()}" for specialty in config.specialties[:3]],
                )

                agent_card = AgentCard(
                    name=config.name.replace("_", " ").title(),
                    description=config.description,
                    url=f"http://localhost:{config.a2a_port}/",
                    version="1.0.0",
                    defaultInputModes=["text"],
                    defaultOutputModes=["text"],
                    capabilities=AgentCapabilities(),
                    skills=[skill],
                )

                request_handler = DefaultRequestHandler(
                    agent_executor=executor,
                    task_store=InMemoryTaskStore(),
                )

                server = A2AStarletteApplication(
                    agent_card=agent_card,
                    http_handler=request_handler
                )

                print(f"🚀 Starting {config.name} A2A server on port {config.a2a_port}")
                uvicorn.run(
                    server.build(),
                    host="0.0.0.0",
                    port=config.a2a_port,
                    timeout_keep_alive=10,
                    log_level="info"
                )
            except Exception as e:
                print(f"❌ Error starting {config.name} server: {e}")

        # Start each server in a separate thread
        print("\n🔄 Starting individual A2A servers...")
        for config in self.agent_configs:
            executor = self.executors[config.executor_class]
            thread = threading.Thread(
                target=start_server,
                args=(config, executor),
                daemon=True
            )
            thread.start()
            time.sleep(1) 
        print("⏳ Waiting for A2A servers to initialize...")
        time.sleep(5)
        print("✅ All A2A servers started successfully!")

    def create_coordinator(self):
        """Create the multi-agent coordinator."""
        print("\n🤖 Creating Multi-Agent Coordinator...")
        a2a_agent_configs = []
        for config in self.agent_configs:
            a2a_config = A2AAgentConfig(
                name=config.name,
                description=config.description,
                url=f"http://localhost:{config.a2a_port}",
                port=config.a2a_port,
                specialties=config.specialties,
                priority=3 if "research" in config.specialties or "coding" in config.specialties else 2
            )
            a2a_agent_configs.append(a2a_config)
        self.coordinator = A2AAdapter(
            name="travel_planner_coordinator",
            description="travel_planner_coordinator - Intelligently routes queries to AI specialists",
            port=8200,
            mailbox=True,
            agent_configs=a2a_agent_configs,
            routing_strategy="keyword_match"
        )

        print("✅ Multi-Agent Coordinator created!")
        print(f"   • Coordinator port: {self.coordinator.port}")
        print(f"   • Managing {len(a2a_agent_configs)} specialist agents")
        print(f"   • Routing strategy: {self.coordinator.routing_strategy}")

        return self.coordinator

    def start_system(self):
        """Start the complete OpenAI multi-agent system."""
        print("🚀 Starting Complete OpenAI Multi-Agent System")
        print("=" * 70)

        try:
            self.setup_agents()

            self.start_individual_a2a_servers()

            coordinator = self.create_coordinator()

            self.display_system_info()

            print(f"\n🎯 Starting coordinator on port {coordinator.port}...")
            print("Press Ctrl+C to stop the system\n")
            
            self.running = True
            coordinator.run()

        except KeyboardInterrupt:
            print("\n👋 Shutting down OpenAI multi-agent system...")
            self.running = False
        except Exception as e:
            print(f"❌ Error starting system: {e}")
            self.running = False

    def display_system_info(self):
        """Display comprehensive system information."""
        print("\n" + "=" * 70)
        print("🤖 OPENAI MULTI-AGENT SYSTEM - READY")
        print("=" * 70)

        print("\n📋 Available AI Specialists:")
        for config in self.coordinator.agent_configs:
            print(f"\n   🔹 {config.name.replace('_', ' ').title()}")
            print(f"      • Specialties: {', '.join(config.specialties)}")
            print(f"      • Auto-generated Keywords: {', '.join(config.keywords[:8])}...")
            print(f"      • Priority: {config.priority}")
            print(f"      • Endpoint: {config.url}")

        print("\n💡 Sample Queries:")

        print(f"\n🌐 Coordinator Address: {self.coordinator.uagent.address}")
        print(f"📡 Coordinator Port: {self.coordinator.port}")

def create_openai_agent_system():
    """Create and return the OpenAI multi-agent system."""
    return OpenAIMultiAgentOrchestrator()

def main():
    """Main function to run the OpenAI multi-agent system."""

    print()

    # Check for OpenAI API key
    import os
    if not os.getenv("OPENAI_API_KEY"):
        return

    print("✅ OpenAI API key found!")
    print()

    # Create and start the system
    try:
        system = create_openai_agent_system()
        system.start_system()
    except KeyboardInterrupt:
        print("\n👋 OpenAI multi-agent system shutdown complete!")
    except Exception as e:
        print(f"\n❌ System error: {e}")

if __name__ == "__main__":
    main()
