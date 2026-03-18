import asyncio
import os
import sys
import json
import structlog
from dotenv import load_dotenv

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

async def run_shopify_test():
    print("Shopify Orchestrator Test (with AKV support)")
    print("-" * 30)
    
    # 1. Setup Settings
    print("Loading Settings...")
    env_path = os.path.join(os.getcwd(), '.env')
    settings = Settings(_env_file=env_path)
    
    # 2. Setup LLM
    print("Initializing LLM...")
    if not settings.OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY missing from .env")
        return
        
    llm = create_provider_from_env(
        provider_name="openai",
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL
    )
    
    # 3. Setup Shopify MCP Tools
    print("Connecting to Shopify MCP Hub (localhost:3005)...")
    shop_url = settings.SHOPIFY_SHOP_URL if hasattr(settings, 'SHOPIFY_SHOP_URL') else os.environ.get("SHOPIFY_SHOP_URL")
    admin_token = settings.SHOPIFY_STOREFRONT_ADMIN_ACCESS_TOKEN if hasattr(settings, 'SHOPIFY_STOREFRONT_ADMIN_ACCESS_TOKEN') else os.environ.get("SHOPIFY_STOREFRONT_ADMIN_ACCESS_TOKEN")
    
    if not shop_url:
        print("Error: SHOPIFY_SHOP_URL missing from config.")
        return
        
    mcp_headers = {
        "x-shopify-shop-url": shop_url,
        "x-shopify-admin-token": admin_token or ""
    }
    
    mcp_endpoint = "http://localhost:3005/mcp"
    mcp_client = McpClient(endpoint=mcp_endpoint, headers=mcp_headers)
    
    registry = ToolRegistry()
    try:
        print(f"Discovering tools for {shop_url}...")
        remote_tools = await mcp_client.discover_tools(session_id="test-session-123")
        for tool in remote_tools:
            registry.register(tool)
            print(f"Registered tool: {tool.name}")
            
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return

    # 3. Setup Orchestrator
    print("\nInitializing Shopify Orchestrator...")
    orchestrator = ShopifyOrchestrator(
        llm=llm,
        tools=registry,
        system_prompt="You are a helpful Shopify shopping assistant."
    )
    
    # Verify the system prompt contains my new instructions
    if "Product Card Format" in orchestrator.system_prompt:
        print("SUCCESS: Product Card Format instructions found in system prompt.")
    else:
        print("FAILURE: Product Card Format instructions NOT found in system prompt.")

    print("\nFinal system prompt snippet:")
    print(orchestrator.system_prompt[-500:])

if __name__ == "__main__":
    asyncio.run(run_shopify_test())
