import asyncio
import os
import sys
import json
import structlog
from dotenv import load_dotenv

# Set encoding for Windows terminal
if sys.platform == "win32":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

# Add local packages to path
sys.path.append(os.path.join(os.getcwd(), 'packages', 'tools', 'src'))
sys.path.append(os.path.join(os.getcwd(), 'packages', 'llm', 'src'))
sys.path.append(os.path.join(os.getcwd(), 'packages', 'agent_runtime', 'src'))
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from tools.mcp_client import McpClient
from tools.registry import ToolRegistry
from llm.factory import create_provider_from_env
from agent_runtime.orchestrator_shopify import ShopifyOrchestrator
from app.config import Settings

async def verify_chaining():
    print("Shopify Chaining Verification: 'add white cricket socks'")
    print("-" * 50)
    
    env_path = os.path.join(os.getcwd(), '.env')
    settings = Settings(_env_file=env_path)
    
    print("Initializing LLM...")
    llm = create_provider_from_env(
        provider_name="openai",
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL
    )
    
    shop_url = settings.SHOPIFY_SHOP_URL
    admin_token = settings.SHOPIFY_STOREFRONT_ADMIN_ACCESS_TOKEN
    
    mcp_headers = {
        "x-shopify-shop-url": shop_url,
        "x-shopify-admin-token": admin_token or ""
    }
    
    print("Connecting to Shopify MCP Hub (localhost:3005)...")
    mcp_endpoint = "http://localhost:3005/mcp"
    mcp_client = McpClient(endpoint=mcp_endpoint, headers=mcp_headers)
    
    registry = ToolRegistry()
    print(f"Discovering tools for {shop_url}...")
    remote_tools = await mcp_client.discover_tools(session_id="verify-chaining-session")
    if not remote_tools:
        print("Error: No tools discovered! Is the MCP hub running?")
        return
        
    for tool in remote_tools:
        registry.register(tool)
        print(f"Registered tool: {tool.name}")
    
    print("Initializing Shopify Orchestrator...")
    orchestrator = ShopifyOrchestrator(
        llm=llm,
        tools=registry,
        system_prompt="You are a helpful Shopify shopping assistant."
    )
    
    # Enable status printing
    async def on_status(msg):
        print(f"STATUS: {msg}")

    query = "add white cricket socks to my cart"
    print(f"\nQuery: {query}")
    
    # Context with a session state
    context = {"session_state": {}}
    
    result = await orchestrator.run(query, context=context, on_status=on_status)
    
    print("\n" + "="*50)
    print("FINAL ANSWER:")
    print("-" * 50)
    print(result.answer)
    print("="*50)
    
    print("\nEXECUTION METADATA:")
    # Custom serializer for ToolResult objects
    def tool_result_serializer(obj):
        from tools.types import ToolResult
        if isinstance(obj, ToolResult):
            return {"success": obj.success, "data": obj.data, "error": obj.error}
        if isinstance(obj, dict):
            return {k: tool_result_serializer(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [tool_result_serializer(i) for i in obj]
        return obj

    serializable_metadata = tool_result_serializer(result.metadata)
    print(json.dumps(serializable_metadata, indent=2))

if __name__ == "__main__":
    asyncio.run(verify_chaining())
