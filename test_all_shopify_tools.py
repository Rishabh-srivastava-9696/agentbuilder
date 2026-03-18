"""
Comprehensive Shopify MCP Tool Test Script
Tests all available tools: Storefront (public) + Customer Account (auth-required)
"""
import asyncio
import json
import uuid
import sys
import os

# Add packages to path
sys.path.append(os.path.join(os.getcwd(), 'packages', 'tools', 'src'))
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from dotenv import load_dotenv
load_dotenv()

from tools.mcp_client import McpClient

MCP_ENDPOINT = "http://localhost:3005/mcp"
SHOP_URL = os.environ.get("SHOPIFY_SHOP_URL", "")
ADMIN_TOKEN = os.environ.get("SHOPIFY_ADMIN_TOKEN", "")
# For customer auth tools - set this to a valid customer access token to test
CUSTOMER_ACCESS_TOKEN = os.environ.get("SHOPIFY_CUSTOMER_ACCESS_TOKEN", "")

MCP_HEADERS = {
    "x-shopify-shop-url": SHOP_URL,
    "x-shopify-admin-token": ADMIN_TOKEN,
}

if CUSTOMER_ACCESS_TOKEN:
    MCP_HEADERS["x-customer-access-token"] = CUSTOMER_ACCESS_TOKEN

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"

results = []

def log_result(tool_name, status, detail=""):
    icon = status
    print(f"  {icon} {tool_name}: {detail}")
    results.append({"tool": tool_name, "status": status, "detail": detail})

async def run_tool(client, session_id, tool_name, **kwargs):
    """Discover tools and execute one by name."""
    tools = await client.discover_tools(session_id=session_id)
    tool = next((t for t in tools if t.name == tool_name), None)
    if not tool:
        return None, f"Tool '{tool_name}' not discovered"
    result = await tool.run(**kwargs)
    return result, None

# ─── TEST STOREFRONT TOOLS ────────────────────────────────────────────────────

async def test_search_shop_catalog(client):
    print("\n[1] search_shop_catalog")
    sid = "test-" + str(uuid.uuid4())[:8]
    result, err = await run_tool(client, sid, "search_shop_catalog",
        query="socks",
        context="User looking for athletic socks"
    )
    if err:
        log_result("search_shop_catalog", FAIL, err)
        return None
    
    if result.success:
        preview = str(result.data)[:200].replace("\n", " ")
        log_result("search_shop_catalog", PASS, f"Got response: {preview}...")
    else:
        log_result("search_shop_catalog", FAIL, f"Error: {result.error}")
    return result


async def test_search_shop_policies_and_faqs(client):
    print("\n[2] search_shop_policies_and_faqs")
    sid = "test-" + str(uuid.uuid4())[:8]
    result, err = await run_tool(client, sid, "search_shop_policies_and_faqs",
        query="return policy",
        context="Customer asking about returns"
    )
    if err:
        log_result("search_shop_policies_and_faqs", FAIL, err)
        return None
    
    if result.success:
        preview = str(result.data)[:200].replace("\n", " ")
        log_result("search_shop_policies_and_faqs", PASS, f"Got response: {preview}...")
    else:
        log_result("search_shop_policies_and_faqs", FAIL, f"Error: {result.error}")
    return result


async def test_update_cart_create(client):
    """Create a new cart by not passing cart_id."""
    print("\n[3] update_cart (create new cart)")
    sid = "test-" + str(uuid.uuid4())[:8]
    
    # First, get a valid variant ID from search
    search_result, _ = await run_tool(client, sid, "search_shop_catalog",
        query="socks",
        context="Test - finding variant ID for cart test"
    )
    
    # Try to extract a variant ID from the text output (or use a placeholder)
    test_variant_id = None
    if search_result and search_result.success:
        data_str = str(search_result.data)
        # Look for common GID patterns in the response
        import re
        match = re.search(r'gid://shopify/ProductVariant/\d+', data_str)
        if match:
            test_variant_id = match.group(0)
    
    if not test_variant_id:
        log_result("update_cart (create)", SKIP, "No variant ID found from search; can't test cart creation")
        return None
    
    result, err = await run_tool(client, sid, "update_cart",
        add_items=[{"product_variant_id": test_variant_id, "quantity": 1}]
    )
    if err:
        log_result("update_cart (create)", FAIL, err)
        return None
    
    if result.success:
        preview = str(result.data)[:300].replace("\n", " ")
        log_result("update_cart (create)", PASS, f"Cart created/updated: {preview}...")
    else:
        log_result("update_cart (create)", FAIL, f"Error: {result.error}")
    return result


async def test_get_cart(client, cart_id=None):
    print("\n[4] get_cart")
    sid = "test-" + str(uuid.uuid4())[:8]
    if not cart_id:
        log_result("get_cart", SKIP, "No cart_id available. Run update_cart first or set SHOPIFY_TEST_CART_ID env var.")
        return None
    
    result, err = await run_tool(client, sid, "get_cart", cart_id=cart_id)
    if err:
        log_result("get_cart", FAIL, err)
        return None
    
    if result.success:
        preview = str(result.data)[:300].replace("\n", " ")
        log_result("get_cart", PASS, f"Cart contents: {preview}...")
    else:
        log_result("get_cart", FAIL, f"Error: {result.error}")
    return result


# ─── TEST CUSTOMER ACCOUNT TOOLS  ─────────────────────────────────────────────

async def test_customer_tool(client, tool_name, label, **kwargs):
    print(f"\n[*] {tool_name} (Auth Required)")
    sid = "test-" + str(uuid.uuid4())[:8]
    
    all_tools = await client.discover_tools(session_id=sid)
    tool = next((t for t in all_tools if t.name == tool_name), None)
    
    if not tool:
        log_result(tool_name, SKIP, f"Not in discovered tool list (likely auth not provided or tool not available)")
        return None
    
    result, err = await run_tool(client, sid, tool_name, **kwargs)
    if err:
        log_result(tool_name, FAIL, err)
        return None
    
    if result.success:
        preview = str(result.data)[:200].replace("\n", " ")
        log_result(tool_name, PASS, f"{label}: {preview}...")
    elif result.error and "Authentication" in str(result.error):
        log_result(tool_name, SKIP, "Auth required - provide SHOPIFY_CUSTOMER_ACCESS_TOKEN to test")
    else:
        log_result(tool_name, FAIL, f"Error: {result.error}")
    return result


# ─── MAIN ─────────────────────────────────────────────────────────────────────

async def main():
    print("=" * 60)
    print("Shopify MCP Tool Test Suite")
    print(f"Endpoint: {MCP_ENDPOINT}")
    print(f"Shop URL: {SHOP_URL}")
    print(f"Customer Auth: {'YES' if CUSTOMER_ACCESS_TOKEN else 'NO (set SHOPIFY_CUSTOMER_ACCESS_TOKEN)'}")
    print("=" * 60)
    
    client = McpClient(endpoint=MCP_ENDPOINT, headers=MCP_HEADERS)
    
    # Discover tools first
    sid = "test-discovery-" + str(uuid.uuid4())[:8]
    tools = await client.discover_tools(session_id=sid)
    print(f"\nDiscovered {len(tools)} tools: {[t.name for t in tools]}")
    
    # --- Storefront (Public) ---
    print("\n--- STOREFRONT TOOLS (Public) ---")
    search_result = await test_search_shop_catalog(client)
    await test_search_shop_policies_and_faqs(client)
    cart_result = await test_update_cart_create(client)
    
    # Try to extract cart_id from update_cart result for get_cart test
    cart_id = os.environ.get("SHOPIFY_TEST_CART_ID")
    if cart_result and cart_result.success:
        import re
        match = re.search(r'gid://shopify/Cart/[^"\'\\s]+', str(cart_result.data))
        if match:
            cart_id = match.group(0)
            print(f"  -> Extracted cart_id: {cart_id}")
    
    await test_get_cart(client, cart_id=cart_id)
    
    # --- Customer Account (Auth Required) ---
    print("\n--- CUSTOMER ACCOUNT TOOLS (Auth Required) ---")
    await test_customer_tool(client, "list_orders", "Orders list")
    await test_customer_tool(client, "get_order", "Order details", order_id="test_order_id")
    await test_customer_tool(client, "track_order", "Tracking info", order_id="test_order_id")
    await test_customer_tool(client, "cancel_order", "Cancel status", order_id="test_order_id")
    await test_customer_tool(client, "get_customer_profile", "Profile data")
    await test_customer_tool(client, "update_customer_profile", "Update result", first_name="Test")
    await test_customer_tool(client, "list_addresses", "Addresses list")
    await test_customer_tool(client, "add_address", "Add address result",
        address={"first_name": "Test", "last_name": "User", "address1": "123 Test St", "city": "Testville", "country_code": "IN"})
    await test_customer_tool(client, "update_address", "Update address result",
        address_id="test_address_id",
        address={"first_name": "Updated"})
    
    # --- Summary ---
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = [r for r in results if r["status"] == PASS]
    failed = [r for r in results if r["status"] == FAIL]
    skipped = [r for r in results if r["status"] == SKIP]
    print(f"  Passed:  {len(passed)}")
    print(f"  Failed:  {len(failed)}")
    print(f"  Skipped: {len(skipped)}")
    if failed:
        print("\nFailed tools:")
        for r in failed:
            print(f"  - {r['tool']}: {r['detail']}")


if __name__ == "__main__":
    asyncio.run(main())
