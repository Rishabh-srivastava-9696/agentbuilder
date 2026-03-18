import asyncio
import json
import os
import sys
import structlog
from typing import List, Dict, Any

# Add packages and app to path
sys.path.append(os.path.join(os.getcwd(), 'packages', 'tools', 'src'))
sys.path.append(os.path.join(os.getcwd(), 'packages', 'llm', 'src'))
sys.path.append(os.path.join(os.getcwd(), 'packages', 'agent_runtime', 'src'))
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv('.env')

from app.config import Settings
from llm.factory import create_provider_from_env
from tools.registry import ToolRegistry
from tools.mcp_client import McpClient
from agent_runtime.orchestrator import Orchestrator

# Configure logging to be less chatty for the CLI
structlog.configure(
    processors=[structlog.processors.JSONRenderer()] if os.environ.get("LOG_FORMAT") == "json" else []
)

async def start_chat():
    print("\n" + "="*60)
    print("🤖 Shopify AI Agent - Natural Language CLI")
    print("="*60)
    print("Type your message to chat with the Shopify assistant.")
    print("Example: 'Find me some socks' or 'What is your refund policy?'")
    print("Type 'exit' to quit.\n")

    settings = Settings()
    
    # 1. Initialize LLM Provider
    # Using settings from .env
    provider_name = settings.DEFAULT_LLM_PROVIDER
    api_key = getattr(settings, f"{provider_name.upper()}_API_KEY")
    model = getattr(settings, f"{provider_name.upper()}_MODEL")
    
    if not api_key:
        print(f"❌ Error: {provider_name.upper()}_API_KEY not found in environment.")
        return

    print(f"🧠 Initializing {provider_name} ({model})...")
    llm = create_provider_from_env(provider_name, api_key, model)

    # 2. Discovery Shopify Tools via MCP
    mcp_endpoint = "http://localhost:3005/mcp"
    
    shop_url = os.environ.get("SHOPIFY_SHOP_URL")
    admin_token = os.environ.get("SHOPIFY_ADMIN_TOKEN")
    
    if not shop_url or not admin_token:
        print("⚠️ Warning: SHOPIFY_SHOP_URL or SHOPIFY_ADMIN_TOKEN missing from .env")
        
    mcp_headers = {
        "x-shopify-shop-url": shop_url or "",
        "x-shopify-admin-token": admin_token or ""
    }
    
    print(f"📡 Connecting to Shopify MCP at {mcp_endpoint} with headers {list(mcp_headers.keys())}...")
    mcp_client = McpClient(endpoint=mcp_endpoint, headers=mcp_headers)
    
    # Register tools
    registry = ToolRegistry()
    remote_tools = await mcp_client.discover_tools(session_id="cli-user-session")
    
    if not remote_tools:
        print("⚠️  Warning: No Shopify tools discovered. Natural language search won't work.")
    else:
        print(f"✅ Registered {len(remote_tools)} Shopify tools.")
        for tool in remote_tools:
            registry.register(tool)

    # 3. Initialize Orchestrator
    system_prompt = """
    You are an expert Shopify Shopping Assistant. 
    You help users find products, understand store policies, and manage their carts.
    Use the search_shop_catalog tool to find products.
    Use the search_shop_policies_and_faqs tool for store information.
    Be helpful, concise, and friendly.
    """
    
    orchestrator = Orchestrator(
        llm=llm,
        tools=registry,
        system_prompt=system_prompt
    )

    history = []

    while True:
        try:
            user_input = input("👤 You: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            if not user_input.strip():
                continue

            print("⏳ Thinking...")
            result = await orchestrator.run(user_input, chat_history=history)
            
            print(f"\n🤖 Agent: {result.answer}")
            
            # Show plan metadata if tools were used
            plan = result.metadata.get("plan", {})
            if plan.get("steps"):
                print(f"   [Used {len(plan['steps'])} tool steps]")

            # Update history
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": result.answer})
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"💥 Error: {str(e)}")

    print("\n👋 Goodbye!")

if __name__ == "__main__":
    try:
        asyncio.run(start_chat())
    except KeyboardInterrupt:
        pass
