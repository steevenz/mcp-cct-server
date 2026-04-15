"""
Multi-Agent CCT Usage Example

Shows how multiple AI agents can share a single CCT server instance.

Usage:
    # 1. First, start the shared server:
    python scripts/server_manager.py start
    
    # 2. Then run this example:
    python examples/multi_agent_example.py
"""
import asyncio
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.server.discover import (
    CCTServerPool, 
    SharedCCTClient,
    get_shared_pool
)


async def agent_think(agent_name: str, problem: str):
    """
    Example of an AI agent using the shared CCT server.
    
    Each agent simply connects to the shared server - no need to start one!
    """
    print(f"\n🤖 Agent '{agent_name}' starting...")
    
    # Option 1: Use shared pool (auto-discovers or starts server)
    # This is the recommended approach for agents
    async with CCTServerPool(auto_start=False) as pool:
        async with pool.get_client() as client:
            # Call the thinking tool
            result = await client.call_tool("thinking", {
                "problem": f"[{agent_name}] {problem}",
                "strategy": "adaptive",
                "profile": "balanced"
            })
            print(f"   ✅ {agent_name} got result: {result}")
            return result
    
    # Option 2: Simple client (assumes server is already running)
    # async with SharedCCTClient() as client:
    #     result = await client.think(problem)
    #     return result


async def concurrent_agents():
    """
    Run multiple agents concurrently using the same shared server.
    """
    print("=" * 60)
    print("🚀 Multi-Agent CCT Example")
    print("=" * 60)
    
    # Define multiple agents with different tasks
    agents = [
        ("Agent-A", "How to optimize Python code performance?"),
        ("Agent-B", "Best practices for API design"),
        ("Agent-C", "Strategies for handling database concurrency"),
    ]
    
    # Run all agents concurrently
    tasks = [
        agent_think(name, problem)
        for name, problem in agents
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    print("\n" + "=" * 60)
    print("📊 Results Summary")
    print("=" * 60)
    
    for (name, _), result in zip(agents, results):
        if isinstance(result, Exception):
            print(f"   ❌ {name}: Failed - {result}")
        else:
            print(f"   ✅ {name}: Completed")
    
    print("\n✨ All agents used the SAME shared CCT server!")


async def shared_pool_demo():
    """
    Demo using the global shared pool across multiple calls.
    """
    print("\n" + "=" * 60)
    print("🔗 Global Shared Pool Demo")
    print("=" * 60)
    
    # Get the global pool - first call initializes it
    pool = await get_shared_pool()
    print(f"   Connected to: {pool.get_server_url()}")
    
    # Simulate multiple agents using the same pool
    for i in range(3):
        print(f"\n   Agent-{i+1} using shared pool...")
        async with pool.get_client() as client:
            # Each agent uses the same underlying server
            pass  # Client operations here
    
    print("\n   ✅ All 3 agents shared one pool connection")


def simple_sync_example():
    """
    Simple synchronous example for quick use.
    
    This shows the easiest way for an agent to check server and use it.
    """
    import httpx
    
    print("\n" + "=" * 60)
    print("📡 Simple HTTP Check")
    print("=" * 60)
    
    # Quick check if server is running
    try:
        response = httpx.get("http://localhost:8001", timeout=2)
        print(f"   ✅ Server is UP (status: {response.status_code})")
        print("   📝 Agents can connect to: http://localhost:8001")
        return True
    except:
        print("   ❌ Server not running")
        print("   🚀 Start with: python scripts/server_manager.py start")
        return False


async def main():
    """Main example runner."""
    # First, simple check
    if not simple_sync_example():
        print("\n⚠️  Please start the server first:")
        print("   python scripts/server_manager.py start")
        return
    
    # Run multi-agent examples
    await concurrent_agents()
    await shared_pool_demo()
    
    print("\n" + "=" * 60)
    print("🎉 Multi-Agent Example Complete!")
    print("=" * 60)
    print("""
Key Takeaways:
1. Start server ONCE: python scripts/server_manager.py start
2. All agents connect to the same server
3. No port conflicts - server manages all connections
4. Agents can use CCTServerPool or simple HTTP
    """)


if __name__ == "__main__":
    asyncio.run(main())
