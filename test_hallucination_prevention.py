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

async def test_hallucination():
    print("Shopify Hallucination Prevention Test")
    print("-" * 50)
    
    env_path = os.path.join(os.getcwd(), '.env')
    settings = Settings(_env_file=env_path)
    
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
    
    mcp_endpoint = "http://localhost:3005/mcp"
    mcp_client = McpClient(endpoint=mcp_endpoint, headers=mcp_headers)
    
    registry = ToolRegistry()
    remote_tools = await mcp_client.discover_tools(session_id="hallucination-test-session")
    for tool in remote_tools:
        registry.register(tool)
    
    orchestrator = ShopifyOrchestrator(
        llm=llm,
        tools=registry,
        system_prompt="You are a helpful Shopify shopping assistant."
    )
    
    context = {"session_state": {}}
    history = []

    # 1. Search for socks
    print("\nTurn 1: 'add white cricket socks to cart'")
    res1 = await orchestrator.run("add white cricket socks to cart", context=context, chat_history=history)
    print(f"Response 1: {res1.answer}")
    history.append({"role": "user", "content": "add white cricket socks to cart"})
    history.append({"role": "assistant", "content": res1.answer})
    
    # Check if results are in session
    has_results = "last_search_results" in context.get("session_state", {})
    print(f"Context has search results: {has_results}")

    # 2. Switch to pants
    print("\nTurn 2: 'pants'")
    res2 = await orchestrator.run("pants", context=context, chat_history=history)
    print(f"Response 2: {res2.answer}")
    
    # CRITICAL CHECK: Did search results clear?
    has_results_after = "last_search_results" in context.get("session_state", {})
    print(f"Context has search results after topic switch: {has_results_after}")
    
    if "socks" in res2.answer.lower() and "pants" not in res2.answer.lower():
        print("❌ FAILURE: Agent hallucinated socks for pants.")
    elif "₹17,000" in res2.answer:
        print("❌ FAILURE: Agent hallucinated a fake total.")
    else:
        print("✅ SUCCESS: No hallucinations detected in topic switch.")

if __name__ == "__main__":
    asyncio.run(test_hallucination())
