"""Multi-agent system using OpenAI models - all AI agents in one terminal."""

import asyncio
import threading
import time
from typing import Dict, List
from dataclasses import dataclass

from uagents_adapter import A2AAdapter
from openai_agents.research_agent import ResearchAgentExecutor
from openai_agents.writing_agent import WritingAgentExecutor
from openai_agents.coding_agent import CodingAgentExecutor
from openai_agents.analysis_agent import AnalysisAgentExecutor


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
    """Orchestrator for multiple OpenAI-powered agents."""
    
    def __init__(self):
        self.agents: Dict[str, A2AAdapter] = {}
        self.agent_configs: Dict[str, OpenAIAgentConfig] = {}
        self.running = False
    
    def register_openai_agent(self, config: OpenAIAgentConfig, executor):
        """Register an OpenAI-powered agent."""
        adapter = A2AAdapter(
            agent_executor=executor,
            name=config.name,
            description=config.description,
            port=config.port,
            a2a_port=config.a2a_port,
            mailbox=True,
            seed=f"{config.name}_seed"
        )
        
        self.agents[config.name] = adapter
        self.agent_configs[config.name] = config
        
        print(f"✅ Registered {config.name}:")
        print(f"   - Description: {config.description}")
        print(f"   - Specialties: {', '.join(config.specialties)}")
        print(f"   - uAgent port: {config.port}")
        print(f"   - A2A port: {config.a2a_port}")
        print()
    
    def start_all_openai_agents(self):
        """Start all OpenAI-powered agents."""
        print("🚀 Starting OpenAI Multi-Agent System")
        print("=" * 60)
        
        threads = []
        
        for name, adapter in self.agents.items():
            print(f"🔄 Starting {name}...")
            
            # Start A2A server
            adapter._start_a2a_server()
            
            # Start uAgent in separate thread
            def run_agent(agent_adapter, agent_name):
                try:
                    print(f"✅ {agent_name} is now running")
                    agent_adapter.uagent.run()
                except Exception as e:
                    print(f"❌ Error running {agent_name}: {e}")
            
            thread = threading.Thread(
                target=run_agent,
                args=(adapter, name),
                daemon=True
            )
            thread.start()
            threads.append(thread)
            
            time.sleep(1)  # Stagger startup
        
        self.running = True
        print("\n🎉 All OpenAI agents are running!")
        print("\n🤖 Available AI Specialists:")
        for name, config in self.agent_configs.items():
            print(f"   • {name}: {', '.join(config.specialties)}")
        
        print("\n💡 Sample Commands:")
        print("   • Research Agent: 'Analyze the impact of AI on healthcare'")
        print("   • Writing Agent: 'WRITE:blog:Future of remote work'")
        print("   • Coding Agent: 'CODE:python:web scraper'")
        print("   • Analysis Agent: 'TRENDS:e-commerce growth 2024'")
        
        print("\nPress Ctrl+C to stop all agents")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down all OpenAI agents...")
            self.running = False


def create_openai_agent_system():
    """Create the complete OpenAI multi-agent system."""
    orchestrator = OpenAIMultiAgentOrchestrator()
    
    # Define OpenAI agent configurations
    agent_configs = [
        OpenAIAgentConfig(
            name="research_specialist",
            description="AI Research Specialist powered by OpenAI GPT-4",
            port=8100,
            a2a_port=10020,
            specialties=["research", "analysis", "fact-finding", "summarization"],
            executor_class="ResearchAgentExecutor"
        ),
        OpenAIAgentConfig(
            name="writing_specialist",
            description="AI Writing Specialist powered by OpenAI GPT-4",
            port=8101,
            a2a_port=10021,
            specialties=["content creation", "editing", "copywriting", "proofreading"],
            executor_class="WritingAgentExecutor"
        ),
        OpenAIAgentConfig(
            name="coding_specialist",
            description="AI Senior Software Engineer powered by OpenAI GPT-4",
            port=8102,
            a2a_port=10022,
            specialties=["code generation", "debugging", "code review", "optimization"],
            executor_class="CodingAgentExecutor"
        ),
        OpenAIAgentConfig(
            name="analysis_specialist",
            description="AI Senior Data Analyst powered by OpenAI GPT-4",
            port=8103,
            a2a_port=10023,
            specialties=["data analysis", "insights", "forecasting", "metrics"],
            executor_class="AnalysisAgentExecutor"
        )
    ]
    
    # Create executors
    executors = {
        "ResearchAgentExecutor": ResearchAgentExecutor(),
        "WritingAgentExecutor": WritingAgentExecutor(),
        "CodingAgentExecutor": CodingAgentExecutor(),
        "AnalysisAgentExecutor": AnalysisAgentExecutor()
    }
    
    # Register all agents
    for config in agent_configs:
        executor = executors[config.executor_class]
        orchestrator.register_openai_agent(config, executor)
    
    return orchestrator


def main():
    """Main function to run the OpenAI multi-agent system."""
    print("🌟 OpenAI Multi-Agent System")
    print("=" * 60)
    print("This system includes AI specialists powered by OpenAI GPT-4:")
    print("🔍 Research Specialist - Information gathering and analysis")
    print("✍️ Writing Specialist - Content creation and editing")
    print("💻 Coding Specialist - Software development and debugging")
    print("📊 Analysis Specialist - Data analysis and insights")
    print()
    print("Each agent uses advanced AI to provide expert-level assistance.")
    print("All agents can collaborate on complex multi-step tasks.")
    print()
    
    # Check for OpenAI API key
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables!")
        print("Please add your OpenAI API key to your .env file:")
        print("OPENAI_API_KEY=your_api_key_here")
        return
    
    # Create and start the system
    system = create_openai_agent_system()
    
    try:
        system.start_all_openai_agents()
    except KeyboardInterrupt:
        print("\n👋 OpenAI multi-agent system shutdown complete!")


if __name__ == "__main__":
    main()
