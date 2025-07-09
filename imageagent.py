
import asyncio
import threading
import time
import os
import logging
from typing import Dict, List
from dataclasses import dataclass

import uvicorn
from dotenv import load_dotenv
from uagent_a2a_adapter import A2AAdapter, A2AAgentConfig

from image_agent.agent import ImageGenerationAgentExecutor



load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    name: str
    description: str
    port: int
    a2a_port: int
    specialties: List[str]
    executor_class: str

class SingleAgent:
    def __init__(self):
        self.coordinator: A2AAdapter = None
        self.agent_configs: List[AgentConfig] = []
        self.executors: Dict[str, any] = {}
        self.running = False

    def setup_agents(self):
        print("🔧 Setting up A2A SingleAgent System\n" + "=" * 60)
        self.agent_configs = [
            AgentConfig(
                name="image_generation_agent",
                description="Generates and edits high-quality images based on user prompts",
                port=8101,
                a2a_port=10001,
                specialties=["generate image", "edit image"],
                executor_class="ImageGenerationAgentExecutor"
            ),
        ]
        self.executors = {"ImageGenerationAgentExecutor": ImageGenerationAgentExecutor()}
        for config in self.agent_configs:
            print(f"✅ {config.name}: {', '.join(config.specialties)}")

    def start_individual_a2a_servers(self):
        from a2a.server.apps import A2AStarletteApplication
        from a2a.server.request_handlers import DefaultRequestHandler
        from a2a.server.tasks import InMemoryTaskStore
        from a2a.types import AgentCapabilities, AgentCard, AgentSkill

        def start_server(config: AgentConfig, executor):
            try:
                skill = AgentSkill(
                    id=f"{config.name.lower()}_skill",
                    name=config.name.replace("_", " ").title(),
                    description=config.description,
                    tags=config.specialties,
                    examples=[f"{s.title()}" for s in config.specialties[:2]],
                )
                agent_card = AgentCard(
                    name=config.name.replace("_", " ").title(),
                    description=config.description,
                    url=f"http://localhost:{config.a2a_port}/",
                    version="1.0.0",
                    defaultInputModes=["text", "text/plain", "image/png"],
                    defaultOutputModes=["text", "text/plain", "image/png"],
                    capabilities=AgentCapabilities(streaming=False),
                    skills=[skill],
                )
                server = A2AStarletteApplication(
                    agent_card=agent_card,
                    http_handler=DefaultRequestHandler(agent_executor=executor, task_store=InMemoryTaskStore())
                )
                print(f"🚀 Starting {config.name} on port {config.a2a_port}")
                uvicorn.run(server.build(), host="0.0.0.0", port=config.a2a_port, timeout_keep_alive=10, log_level="info")
            except Exception as e:
                print(f"❌ Error starting {config.name}: {e}")

        print("\n🔄 Starting A2A servers...")
        for config in self.agent_configs:
            executor = self.executors[config.executor_class]
            threading.Thread(target=start_server, args=(config, executor), daemon=True).start()
            time.sleep(1)
        print("⏳ Initializing servers..."), time.sleep(5), print("✅ All A2A servers started!")

    def create_coordinator(self):
        print("\n🤖 Creating Coordinator...")
        a2a_configs = [
            A2AAgentConfig(
                name=c.name,
                description=c.description,
                url=f"http://localhost:{c.a2a_port}",
                port=c.a2a_port,
                specialties=c.specialties,
                priority=2
            ) for c in self.agent_configs
        ]
        self.coordinator = A2AAdapter(
            name="image_generation_coordinator",
            description="Routes queries to Image Generation Agent",
            port=8200,
            mailbox=True,
            agent_configs=a2a_configs,
            routing_strategy="keyword_match"
        )
        print(f"✅ Coordinator on port {self.coordinator.port} with {len(a2a_configs)} agents")
        return self.coordinator

    def start_system(self):
        print("🚀 Starting A2A System\n" + "=" * 70)
        try:
            self.setup_agents()
            self.start_individual_a2a_servers()
            coordinator = self.create_coordinator()
            self.display_system_info()
            print(f"\n🎯 Running coordinator on port {coordinator.port}...\nPress Ctrl+C to stop\n")
            self.running = True
            coordinator.run()
        except KeyboardInterrupt:
            print("\n👋 System shutdown..."); self.running = False
        except Exception as e:
            print(f"❌ Error: {e}"); self.running = False

    def display_system_info(self):
        print("\n" + "=" * 70 + "\n🤖 SYSTEM READY\n" + "=" * 70)
        for config in self.coordinator.agent_configs:
            print(f"\n🔹 {config.name.replace('_', ' ').title()}")
            print(f"   • Specialties: {', '.join(config.specialties)}")
            print(f"   • Keywords: {', '.join(config.keywords[:8])}...")
            print(f"   • Priority: {config.priority}")
            print(f"   • Endpoint: {config.url}")
        print(f"\n🌐 Coordinator Address: {self.coordinator.uagent.address}")
        print(f"📡 Port: {self.coordinator.port}")

def main():
    try:
        if not os.getenv('GOOGLE_API_KEY') and not os.getenv('GOOGLE_GENAI_USE_VERTEXAI'):
            raise Exception("GOOGLE_API_KEY or GOOGLE_GENAI_USE_VERTEXAI environment variable not set.")
        system = SingleAgent()
        system.start_system()
    except KeyboardInterrupt:
        print("\n👋 Shutdown complete!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()