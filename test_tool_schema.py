import asyncio
import json
import uuid
import sys
import os

# Add packages to path
sys.path.append(os.path.join(os.getcwd(), 'packages', 'tools', 'src'))
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from tools.mcp_client import McpClient

async def run_schema_test():
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
    
    try:
        tools = await client.discover_tools(session_id="test-schema-" + str(uuid.uuid4())[:8])
        search_tool = next((t for t in tools if t.name == "search_shop_catalog"), None)
        if search_tool:
            print(f"🛠 Tool: {search_tool.name}")
            print(f"📋 Full Schema: {json.dumps(search_tool.parameters_schema, indent=2)}")
        else:
            print("❌ search_shop_catalog not found.")
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_schema_test())
