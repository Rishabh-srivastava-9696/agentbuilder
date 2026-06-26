"""
Retrieval Tool - Wraps the RetrievalPipeline for agent use.
"""

import re
from typing import Optional, Dict, Any, List
from tools.types import BaseTool, ToolResult
from retrieval.pipeline import RetrievalPipeline
from retrieval.types import RetrievalContext

class RetrievalTool(BaseTool):
    """
    Tool that grants agents access to the RAG retrieval pipeline.
    """
    
    name = "knowledge_search"
    description = "Searches the internal knowledge base for relevant information about products, support, policies, or other facts."
    
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find information. Be specific."
            },
            "filters": {
                "type": "object",
                "description": "Optional filters like {'content_type': 'product'}"
            }
        },
        "required": ["query"]
    }
    
    def __init__(self, retrieval_pipeline: RetrievalPipeline):
        self.pipeline = retrieval_pipeline
        self.page_context: Optional[Dict[str, Any]] = None
        
    async def run(self, query: str, filters: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        """Run the retrieval pipeline."""
        try:
            context: RetrievalContext = await self.pipeline.retrieve(
                query=query,
                page_context=kwargs.get("page_context") or self.page_context,
                filters=filters or {},
                max_chunks=5  # Tool usage usually needs concise top results
            )
            
            # Format the output for the agent
            if not context.chunks:
                return ToolResult(
                    success=True, 
                    data="No relevant information found in the knowledge base.",
                    metadata={
                        "confidence": 0.0,
                        "products": [],
                        "dealers": []
                    }
                )
            
            # Extract structured data from chunks
            products = self._extract_products(context.chunks)
            dealers = self._extract_dealers(context.chunks)
                
            # Create a string representation of the chunks
            results_text = "Found the following information:\n\n"
            for i, chunk in enumerate(context.chunks, 1):
                content = getattr(chunk, 'text', '') or getattr(chunk, 'content', '')
                source = chunk.doc_id
                results_text += f"[{i}] source_id: {source}\n{content[:500]}...\n\n"
                
            return ToolResult(
                success=True,
                data=results_text,
                metadata={
                    "confidence": context.confidence,
                    "sources": context.sources,
                    "chunks_count": len(context.chunks),
                    "products": products,
                    "dealers": dealers
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                metadata={
                    "products": [],
                    "dealers": []
                }
            )
    
    def _extract_products(self, chunks: List[Any]) -> List[Dict[str, Any]]:
        """Extract product data from retrieval chunks.
        
        DocumentChunk has product_data as a top-level attribute, not inside metadata.
        """
        products = []
        seen_ids = set()
        
        for chunk in chunks:
            # product_data is a top-level attribute on DocumentChunk
            product_data = getattr(chunk, 'product_data', None)
            
            if product_data and isinstance(product_data, dict):
                # Use SKU as the unique ID for deduplication
                product_id = product_data.get('sku') or product_data.get('product_id') or product_data.get('id')
                
                if product_id and product_id not in seen_ids:
                    seen_ids.add(product_id)
                    # Start with all product data
                    product_item = product_data.copy()
                    
                    # Update with normalized keys expected by frontend
                    product_item.update({
                        "id": product_id,
                        "sku": product_id,  # Ensure SKU is explicit
                        "name": product_data.get('name'),
                        "description": product_data.get('category', ''),
                        "price": product_data.get('price'),
                        "image": product_data.get('image_url'),
                        "url": product_data.get('product_url')
                    })
                    products.append(product_item)
        
        return products
    
    def _extract_dealers(self, chunks: List[Any]) -> List[Dict[str, Any]]:
        """Extract dealer data from retrieval chunks.
        
        DocumentChunk has dealer_data as a top-level attribute, not inside metadata.
        """
        dealers = []
        seen_ids = set()
        
        for chunk in chunks:
            # dealer_data is a top-level attribute on DocumentChunk
            dealer_data = getattr(chunk, 'dealer_data', None)
            
            if dealer_data and isinstance(dealer_data, dict):
                dealer_id = dealer_data.get('dealer_id') or dealer_data.get('id')
                
                if dealer_id and dealer_id not in seen_ids:
                    seen_ids.add(dealer_id)
                    
                    # Start with all dealer data
                    dealer_item = dealer_data.copy()
                    
                    # Update with normalized keys
                    dealer_item.update({
                        "id": dealer_id,
                        "name": dealer_data.get('name'),
                        "address": dealer_data.get('address'),
                        "phone": dealer_data.get('phone'),
                        "location": dealer_data.get('city')
                    })
                    dealers.append(dealer_item)
        
        return dealers


class CatalogSearchTool(RetrievalTool):
    """Shopify-compatible catalog search backed by NOVA's synced product RAG."""

    description = "Searches NOVA's synced Shopify product catalog for product recommendations, prices, images, and product URLs."

    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The product search query, including budget or product type constraints when present."
            },
            "filters": {
                "type": "object",
                "description": "Optional catalog filters."
            },
            "pagination": {
                "type": "object",
                "description": "Optional pagination settings such as {'limit': 10}."
            }
        },
        "required": ["query"]
    }

    def __init__(self, retrieval_pipeline: RetrievalPipeline, name: str = "search_catalog"):
        super().__init__(retrieval_pipeline)
        self.name = name

    async def run(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ToolResult:
        budget = self._extract_max_budget(query)
        limit = self._pagination_limit(pagination)
        if budget is not None:
            budget_products = await self._direct_budget_products(query, budget, limit)
            if budget_products:
                return ToolResult(
                    success=True,
                    data=self._format_catalog_results(budget_products),
                    metadata={
                        "confidence": 0.95,
                        "products": budget_products,
                        "dealers": [],
                        "tool_id": self.name,
                        "search_query": query,
                        "budget_filter": {"max_amount": budget, "currency": "INR"},
                        **({"pagination": pagination} if pagination else {}),
                    },
                )

        product_filters = {"content_type": "product", **(filters or {})}
        result = await super().run(query=query, filters=product_filters, **kwargs)
        if result.metadata is not None:
            result.metadata["tool_id"] = self.name
            result.metadata["search_query"] = query
            if pagination:
                result.metadata["pagination"] = pagination
            products = result.metadata.get("products") or []
            if result.success and products:
                result.data = self._format_catalog_results(products)
        return result

    def _format_catalog_results(self, products: List[Dict[str, Any]]) -> str:
        lines = ["Found catalog products:"]
        for index, product in enumerate(products[:5], start=1):
            name = product.get("name") or product.get("title") or product.get("sku") or "Product"
            price = self._display_price(product.get("price"), product.get("currency"))
            category = product.get("category") or product.get("description") or "General"
            sku = product.get("sku") or product.get("id")
            lines.append(f"{index}. {name} - {price} ({category}, SKU: {sku})")
        return "\n".join(lines)

    def _display_price(self, price: Any, currency: Any) -> str:
        try:
            numeric_price = float(price)
            display_price = numeric_price / 100 if numeric_price >= 10000 else numeric_price
            amount = f"{int(display_price):,}" if display_price.is_integer() else f"{display_price:,.2f}"
        except (TypeError, ValueError):
            amount = str(price or "0")
        return f"{currency or 'INR'} {amount}"

    def _extract_max_budget(self, query: str) -> Optional[float]:
        lowered = (query or "").lower()
        if not re.search(r"\b(under|below|less than|within|budget|max|maximum|upto|up to)\b|[₹₨]", lowered):
            return None
        match = re.search(
            r"(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*(?:\.\d+)?)\s*(k|thousand|lakh|lac)?\b",
            lowered,
        )
        if not match:
            return None
        amount = float(match.group(1).replace(",", ""))
        suffix = (match.group(2) or "").strip()
        if suffix in {"k", "thousand"}:
            amount *= 1_000
        elif suffix in {"lakh", "lac"}:
            amount *= 100_000
        return amount

    def _pagination_limit(self, pagination: Optional[Dict[str, Any]]) -> int:
        if isinstance(pagination, dict):
            try:
                return max(1, min(int(pagination.get("limit") or 5), 10))
            except (TypeError, ValueError):
                pass
        return 5

    async def _direct_budget_products(self, query: str, budget: float, limit: int) -> List[Dict[str, Any]]:
        collection = self._catalog_collection()
        if collection is None:
            return []

        pattern = self._catalog_pattern(query)
        max_minor_units = int(budget * 100)
        mongo_query: Dict[str, Any] = {
            "content_type": "product",
            "product_data.price": {"$gt": 0, "$lte": max_minor_units},
        }
        if pattern:
            mongo_query["$or"] = [
                {"title": {"$regex": pattern, "$options": "i"}},
                {"content": {"$regex": pattern, "$options": "i"}},
                {"product_data.name": {"$regex": pattern, "$options": "i"}},
                {"product_data.category": {"$regex": pattern, "$options": "i"}},
                {"product_data.features": {"$regex": pattern, "$options": "i"}},
            ]

        cursor = collection.find(
            mongo_query,
            {"product_data": 1, "title": 1, "content": 1, "doc_id": 1},
        ).sort("product_data.price", -1).limit(limit * 8)
        rows = await cursor.to_list(length=limit * 8)

        products: List[Dict[str, Any]] = []
        seen = set()
        lowered_query = (query or "").lower()
        for row in rows:
            product_data = row.get("product_data") or {}
            product_id = product_data.get("sku") or product_data.get("product_id") or product_data.get("id")
            if not product_id or product_id in seen:
                continue
            name = str(product_data.get("name") or row.get("title") or "")
            if not re.search(r"\bcables?\b", lowered_query) and re.search(r"\b(cables?|wire|interconnect|banana plug)\b", name, re.I):
                continue
            seen.add(product_id)
            currency = product_data.get("currency") or "INR"
            if str(currency).upper() == "USD" and "usd" not in lowered_query:
                currency = "INR"
            item = dict(product_data)
            item.update({
                "id": product_id,
                "sku": product_id,
                "name": name,
                "description": product_data.get("category", ""),
                "price": product_data.get("price"),
                "currency": currency,
                "image": product_data.get("image_url"),
                "url": product_data.get("product_url"),
                "matched_constraints": [f"under budget {budget:g}"],
                "missing_constraints": [],
                "reason": f"Priced under {self._display_price(budget * 100, 'INR')}.",
            })
            products.append(item)
            if len(products) >= limit:
                break
        return products

    def _catalog_collection(self):
        bm25 = getattr(self.pipeline, "bm25_search", None)
        collection = getattr(bm25, "collection", None)
        if collection is not None:
            return collection
        vector = getattr(self.pipeline, "vector_search", None)
        return getattr(vector, "collection", None)

    def _catalog_pattern(self, query: str) -> str:
        lowered = (query or "").lower()
        audio_terms = [
            "audio", "sound", "speaker", "speakers", "amplifier", "subwoofer",
            "receiver", "preamplifier", "network player", "wireless speaker",
            "home theater", "home theatre", "cinema", "system", "systems",
        ]
        matched = [re.escape(term) for term in audio_terms if term in lowered]
        if "audio" in lowered or "sound" in lowered or "system" in lowered:
            matched.extend([
                "audio", "sound", "speaker", "amplifier", "subwoofer",
                "receiver", "preamplifier", "network player", "wireless speaker",
                "home theater", "home theatre", "cinema",
            ])
        return "|".join(sorted(set(matched), key=len, reverse=True))
