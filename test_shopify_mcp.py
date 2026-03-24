import asyncio
import json
import uuid
import sys
import os

# Add packages to path so we can import tools
sys.path.append(os.path.join(os.getcwd(), 'packages', 'tools', 'src'))
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from tools.mcp_client import McpClient

async def run_test_cli():
    print("🚀 Shopify MCP Local CLI Tester")
    print("-" * 30)
    
    endpoint = "http://localhost:3005/mcp"
    
    from dotenv import load_dotenv
    load_dotenv()
    
    shop_url = os.environ.get("SHOPIFY_SHOP_URL")
    admin_token = os.environ.get("SHOPIFY_ADMIN_TOKEN")
    
    if not shop_url or not admin_token:
        print("⚠️ Warning: SHOPIFY_SHOP_URL or SHOPIFY_ADMIN_TOKEN is missing from .env.")
        print("    Tool calls may fail with AuthRequired errors!")
        
    mcp_headers = {
        "x-shopify-shop-url": shop_url or "",
        "x-shopify-admin-token": admin_token or ""
    }
    
    client = McpClient(endpoint=endpoint, headers=mcp_headers)
    
    print(f"📡 Connecting to {endpoint} with headers {list(mcp_headers.keys())}...")
    tools = await client.discover_tools(session_id="test-session-" + str(uuid.uuid4())[:8])
    
    if not tools:
        print("❌ No tools discovered. Is the Node.js service running on port 3005?")
        return

    print(f"✅ Discovered {len(tools)} tools:")
    for i, tool in enumerate(tools):
        print(f"  {i+1}. {tool.name}: {tool.description}")
    
    while True:
        print("\n" + "="*50)
        choice = input("Enter tool number to call (or 'q' to quit): ")
        if choice.lower() == 'q':
            break
            
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(tools):
                print("Invalid choice.")
                continue
                
            selected_tool = tools[idx]
            print(f"\n🛠 Testing Tool: {selected_tool.name}")
            print(f"📋 Schema: {json.dumps(selected_tool.parameters_schema, indent=2)}")
            
            args_str = input("Enter arguments as JSON (e.g. {\"query\": \"socks\"}) or press Enter for empty: ")
            args = {}
            if args_str.strip():
                try:
                    args = json.loads(args_str)
                except json.JSONDecodeError:
                    print("❌ Invalid JSON format.")
                    continue
            
            print(f"📤 Calling {selected_tool.name} with {args}...")
            result = await selected_tool.run(**args)
            
            if result.success:
                print("🟢 Success!")
                print(f"📥 Result Data: {result.data}")
            else:
                print("🔴 Failed!")
                print(f"❌ Error: {result.error}")
                
        except ValueError:
            print("Please enter a number.")
        except Exception as e:
            print(f"💥 Runtime Error: {str(e)}")

if __name__ == "__main__":
    if not os.path.exists('packages/tools'):
        print("❌ Error: Please run this script from the root 'agentbuilder' directory.")
        sys.exit(1)
        
    try:
        asyncio.run(run_test_cli())
    except KeyboardInterrupt:
        print("\nExiting...")
