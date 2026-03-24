"""
Probe what tools the Shopify Customer Account MCP actually offers
when a valid Bearer token is provided.
"""
import os, asyncio, json
from dotenv import load_dotenv
import httpx

async def run():
    load_dotenv()
    shop_url = os.environ.get("SHOPIFY_SHOP_URL", "").replace("https://", "").rstrip("/")
    token = os.environ.get("SHOPIFY_CUSTOMER_ACCESS_TOKEN", "")
    
    if not token:
        print("ERROR: SHOPIFY_CUSTOMER_ACCESS_TOKEN not set in .env")
        return
    
    # Discover customer account MCP endpoint
    discovery_url = f"https://{shop_url}/.well-known/customer-account-api"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(discovery_url)
        config = r.json() if r.is_success else {}
    
    customer_mcp = config.get("mcp_api") or f"https://{shop_url}/customer/api/mcp"
    print(f"Customer Account MCP endpoint: {customer_mcp}")
    
    # Try to list tools with Bearer auth
    payload = {"jsonrpc": "2.0", "id": "probe-1", "method": "tools/list", "params": {}}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            customer_mcp,
            json=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        )
    
    print(f"Status: {r.status_code}")
    body = r.json() if r.is_success else r.text
    if isinstance(body, dict) and "result" in body:
        tools = body["result"].get("tools", [])
        print(f"\nCustomer Account MCP Tools ({len(tools)} total):")
        for t in tools:
            print(f"  - {t['name']}: {t.get('description','')[:80]}")
    else:
        print("Response:", str(body)[:500])

if __name__ == "__main__":
    asyncio.run(run())
