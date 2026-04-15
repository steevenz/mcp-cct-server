import pytest
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client

@pytest.mark.skip(reason="pytest-asyncio plugin not installed")
async def test_cct_sse():
    print("Testing CCT MCP Server via SSE...")
    async with sse_client("http://localhost:8001/sse") as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize session
            await session.initialize()
            print("Session initialized.")
            
            # List tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")
            
            # Call 'thinking' tool
            print("Calling 'thinking' tool...")
            result = await session.call_tool("thinking", {
                "problem_statement": "Bagaimana cara membuat sistem transportasi yang efisien di Jakarta?",
                "profile": "creative"
            })
            print(f"Thinking result: {result}")
            
            if hasattr(result, 'content') and result.content:
                # Assuming result.content is a list of TextContent
                import json
                try:
                    res_json = json.loads(result.content[0].text)
                    session_id = res_json.get("session_id")
                    print(f"Session created: {session_id}")
                    
                    if session_id:
                        # Call 'rethinking' tool
                        print(f"Calling 'rethinking' tool for session {session_id}...")
                        rethinking_result = await session.call_tool("rethinking", {
                            "session_id": session_id,
                            "thought_content": "Mari kita pertimbangkan opsi transportasi berbasis air (sungai).",
                            "thought_number": 2
                        })
                        print(f"Rethinking result: {rethinking_result}")
                        
                        # Call 'list_thinking' tool
                        print("Calling 'list_thinking' tool...")
                        list_result = await session.call_tool("list_thinking", {})
                        print(f"List sessions result: {list_result}")
                except Exception as e:
                    print(f"Error parsing result: {e}")

if __name__ == "__main__":
    asyncio.run(test_cct_sse())
