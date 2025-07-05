"""Multi-agent file processing system - all specialized file agents in one terminal."""

import asyncio
import threading
import time
from typing import Dict, List
from dataclasses import dataclass

from uagents_adapter import A2AAdapter
from file_agents.text_agent import TextProcessorExecutor
from file_agents.json_agent import JSONProcessorExecutor
from file_agents.csv_agent import CSVProcessorExecutor
from file_agents.code_agent import CodeProcessorExecutor


@dataclass
class FileAgentConfig:
    """Configuration for a file processing agent."""
    name: str
    description: str
    port: int
    a2a_port: int
    file_types: List[str]
    executor_class: str


class MultiFileAgentOrchestrator:
    """Orchestrator for multiple specialized file processing agents."""
    
    def __init__(self):
        self.agents: Dict[str, A2AAdapter] = {}
        self.agent_configs: Dict[str, FileAgentConfig] = {}
        self.running = False
    
    def register_file_agent(self, config: FileAgentConfig, executor):
        """Register a file processing agent."""
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
        print(f"   - File Types: {', '.join(config.file_types)}")
        print(f"   - uAgent port: {config.port}")
        print(f"   - A2A port: {config.a2a_port}")
        print()
    
    def start_all_file_agents(self):
        """Start all file processing agents."""
        print("🚀 Starting Multi-Agent File Processing System")
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
        print("\n🎉 All file processing agents are running!")
        print("\n📋 Available Agents:")
        for name, config in self.agent_configs.items():
            print(f"   • {name}: {', '.join(config.file_types)}")
        
        print("\n💡 Usage Examples:")
        print("   • Text Agent: CREATE_TEXT:sample:story")
        print("   • JSON Agent: CREATE_JSON:data:users")
        print("   • CSV Agent: CREATE_CSV:sales:sales")
        print("   • Code Agent: CREATE_CODE:app:python")
        
        print("\nPress Ctrl+C to stop all agents")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down all file processing agents...")
            self.running = False


def create_file_processing_system():
    """Create the complete file processing agent system."""
    orchestrator = MultiFileAgentOrchestrator()
    
    # Define specialized file agent configurations
    agent_configs = [
        FileAgentConfig(
            name="text_processor_agent",
            description="Specialized agent for text file processing and analysis",
            port=8090,
            a2a_port=10010,
            file_types=[".txt", ".md"],
            executor_class="TextProcessorExecutor"
        ),
        FileAgentConfig(
            name="json_processor_agent",
            description="Specialized agent for JSON file processing and validation",
            port=8091,
            a2a_port=10011,
            file_types=[".json"],
            executor_class="JSONProcessorExecutor"
        ),
        FileAgentConfig(
            name="csv_processor_agent",
            description="Specialized agent for CSV file processing and analysis",
            port=8092,
            a2a_port=10012,
            file_types=[".csv"],
            executor_class="CSVProcessorExecutor"
        ),
        FileAgentConfig(
            name="code_processor_agent",
            description="Specialized agent for code file processing and analysis",
            port=8093,
            a2a_port=10013,
            file_types=[".py", ".js", ".ts", ".java", ".cpp", ".c"],
            executor_class="CodeProcessorExecutor"
        )
    ]
    
    # Create executors
    executors = {
        "TextProcessorExecutor": TextProcessorExecutor(),
        "JSONProcessorExecutor": JSONProcessorExecutor(),
        "CSVProcessorExecutor": CSVProcessorExecutor(),
        "CodeProcessorExecutor": CodeProcessorExecutor()
    }
    
    # Register all agents
    for config in agent_configs:
        executor = executors[config.executor_class]
        orchestrator.register_file_agent(config, executor)
    
    return orchestrator


def main():
    """Main function to run the multi-agent file processing system."""
    print("🌟 Multi-Agent File Processing System")
    print("=" * 60)
    print("This system includes specialized agents for:")
    print("📄 Text Agent - .txt, .md files (analysis, search, readability)")
    print("📋 JSON Agent - .json files (validation, querying, transformation)")
    print("📊 CSV Agent - .csv files (statistics, analysis, querying)")
    print("💻 Code Agent - .py, .js, .ts, .java, .cpp files (linting, complexity)")
    print()
    print("Each agent runs independently but can be coordinated for complex workflows.")
    print()
    
    # Create and start the system
    system = create_file_processing_system()
    
    try:
        system.start_all_file_agents()
    except KeyboardInterrupt:
        print("\n👋 Multi-agent file processing system shutdown complete!")


if __name__ == "__main__":
    main()
