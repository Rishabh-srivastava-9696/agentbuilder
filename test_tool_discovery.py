import asyncio
import json
import uuid
import sys
import os

# Add packages to path
sys.path.append(os.path.join(os.getcwd(), 'packages', 'tools', 'src'))
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from tools.mcp_client import McpClient

async def run_discovery_test():
    endpoint = "http://localhost:3005/mcp"
    
    from dotenv import load_dotenv
    load_dotenv()
    
    shop_url = os.environ.get("SHOPIFY_SHOP_URL")
    admin_token = os.environ.get("SHOPIFY_ADMIN_TOKEN")
    
    mcp_headers = {
        "x-shopify-shop-url": shop_url or "",
        "x-shopify-admin-token": admin_token or ""
    }
    
    client = McpClient(endpoint=endpoint, headers=mcp_headers)
    
    print(f"📡 Discovering tools from {endpoint}...")
    try:
        tools = await client.discover_tools(session_id="test-discovery-" + str(uuid.uuid4())[:8])
        
        if not tools:
            print("❌ No tools discovered.")
            return

        print(f"✅ Discovered {len(tools)} tools:")
        for i, tool in enumerate(tools):
            print(f"  - {tool.name}: {tool.description}")
            
        # Try calling the retrieval/search tool if it exists
        search_tool = next((t for t in tools if t.name in ["retrieval", "search_shop_catalog"]), None)
        if search_tool:
            print(f"\n🛠 Testing Tool: {search_tool.name}")
            result = await search_tool.run(query="socks")
            print(f"📥 Result Success: {result.success}")
            print(f"📥 Result Data: {json.dumps(result.data, indent=2)[:500]}...")
        else:
            print("\n⚠️ No search tool found in the list.")
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_discovery_test())
