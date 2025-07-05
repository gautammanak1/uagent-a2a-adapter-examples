

from dotenv import load_dotenv

from codeagent.a2agent import AdvancedAgentExecutor
from uagents_adapter import A2AAdapter


# Load environment variables
load_dotenv()

def main():
    """Main function to run the advanced A2A agent."""

    executor = AdvancedAgentExecutor()

    adapter = A2AAdapter(
        agent_executor=executor,
        name="advanced_a2a_agent",
        description="An advanced A2A agent with enhanced capabilities",
        port=8082,
        a2a_port=9997,
        mailbox=True,
        seed="advanced"
    )

    print("🚀 Starting Advanced A2A Agent...")
    print("📝 Features:")
    print("  - Detailed explanations")
    print("  - Code examples")
    print("  - Step-by-step solutions")
    print("  - Context awareness")
    print()

    adapter.run()

if __name__ == "__main__":
    main()  
