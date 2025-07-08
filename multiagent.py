import asyncio
import threading
import time
from typing import Dict, List
from dataclasses import dataclass
from adpter import A2AAdapter, A2AAgentConfig
from agents.research_agent import ResearchAgentExecutor
from agents.coding_agent import CodingAgentExecutor
from agents.analysis_agent import AnalysisAgentExecutor

@dataclass
class AIAgentConfig:
    name: str
    description: str
    port: int
    a2a_port: int
    specialties: List[str]
    executor_class: str

class MultiAgentOrchestrator:
    def __init__(self):
        self.coordinator = None
        self.agent_configs: List[AIAgentConfig] = []
        self.executors: Dict[str, any] = {}
        self.running = False

    def setup_agents(self):
        print("🔧 Setting up Multi-Agent System")
        self.agent_configs = [
            AIAgentConfig(
                name="research_specialist",
                description="AI Research Specialist for research and analysis",
                port=8100,
                a2a_port=10020,
                specialties=["research", "analysis", "fact-finding", "summarization"],
                executor_class="ResearchAgentExecutor"
            ),
            AIAgentConfig(
                name="coding_specialist",
                description="AI Software Engineer for coding",
                port=8102,
                a2a_port=10022,
                specialties=["coding", "debugging", "programming"],
                executor_class="CodingAgentExecutor"
            ),
            AIAgentConfig(
                name="analysis_specialist",
                description="AI Data Analyst for insights and metrics",
                port=8103,
                a2a_port=10023,
                specialties=["data analysis", "insights", "forecasting"],
                executor_class="AnalysisAgentExecutor"
            )
        ]
        self.executors = {
            "ResearchAgentExecutor": ResearchAgentExecutor(),
            "CodingAgentExecutor": CodingAgentExecutor(),
            "AnalysisAgentExecutor": AnalysisAgentExecutor()
        }
        print("✅ Agent configurations created")

    def start_individual_a2a_servers(self):
        from a2a.server.apps import A2AStarletteApplication
        from a2a.server.request_handlers import DefaultRequestHandler
        from a2a.server.tasks import InMemoryTaskStore
        from a2a.types import AgentCapabilities, AgentCard, AgentSkill
        import uvicorn

        def start_server(config: AIAgentConfig, executor):
            try:
                skill = AgentSkill(
                    id=f"{config.name}_skill",
                    name=config.name.title(),
                    description=config.description,
                    tags=config.specialties
                )
                agent_card = AgentCard(
                    name=config.name.title(),
                    description=config.description,
                    url=f"http://localhost:{config.a2a_port}/",
                    version="1.0.0",
                    defaultInputModes=["text"],
                    defaultOutputModes=["text"],
                    capabilities=AgentCapabilities(),
                    skills=[skill]
                )
                server = A2AStarletteApplication(
                    agent_card=agent_card,
                    http_handler=DefaultRequestHandler(
                        agent_executor=executor,
                        task_store=InMemoryTaskStore()
                    )
                )
                print(f"🚀 Starting {config.name} server on port {config.a2a_port}")
                uvicorn.run(server.build(), host="0.0.0.0", port=config.a2a_port, log_level="info")
            except Exception as e:
                print(f"❌ Error starting {config.name} server: {e}")

        print("🔄 Starting servers...")
        for config in self.agent_configs:
            thread = threading.Thread(
                target=start_server,
                args=(config, self.executors[config.executor_class]),
                daemon=True
            )
            thread.start()
            time.sleep(1)
        time.sleep(5)
        print("✅ Servers started!")

    def create_coordinator(self):
        print("🤖 Creating Coordinator...")
        a2a_configs = [
            A2AAgentConfig(
                name=config.name,
                description=config.description,
                url=f"http://localhost:{config.a2a_port}",
                port=config.a2a_port,
                specialties=config.specialties,
                priority=3 if "research" in config.specialties or "coding" in config.specialties else 2
            ) for config in self.agent_configs
        ]
        self.coordinator = A2AAdapter(
            name="coordinator",
            description="Routes queries to AI specialists",
            port=8200,
            mailbox=True,
            agent_configs=a2a_configs,
            routing_strategy="keyword_match"
        )
        print("✅ Coordinator created!")
        return self.coordinator

    def start_system(self):
        print("🚀 Starting Multi-Agent System")
        try:
            self.setup_agents()
            self.start_individual_a2a_servers()
            coordinator = self.create_coordinator()
            self.running = True
            print(f"🎯 Starting coordinator on port {coordinator.port}...")
            coordinator.run()
        except KeyboardInterrupt:
            print("👋 Shutting down...")
            self.running = False
        except Exception as e:
            print(f"❌ Error: {e}")
            self.running = False

def main():
    try:
        system = MultiAgentOrchestrator()
        system.start_system()
    except KeyboardInterrupt:
        print("👋 Shutdown complete!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()