"""
Response models for the Agent Builder Platform API
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class Citation(BaseModel):
    """Citation information."""
    doc_id: str
    title: Optional[str] = None
    url: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    snippet: Optional[str] = None


CurrencySource = Literal["shopify_store", "catalog", "presentment", "configured_default", "missing"]


class CommerceCart(BaseModel):
    """Canonical cart state emitted by commerce-capable agents."""
    cart_id: Optional[str] = None
    checkout_url: Optional[str] = None
    cart_lines: List[Dict[str, Any]] = Field(default_factory=list)


class ProductVariant(BaseModel):
    """Stable, minor-unit product variant contract for widget cards."""
    id: Optional[str] = None
    variant_id: Optional[str] = None
    sku: Optional[str] = None
    variant_sku: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    variant_title: Optional[str] = None
    variant_options: Dict[str, str] = Field(default_factory=dict)
    price_minor: Optional[int] = None
    price: Optional[int] = None  # Legacy input compatibility only.
    price_unit: Literal["minor"] = "minor"
    currency: Optional[str] = None
    currency_source: Optional[CurrencySource] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    variant_url: Optional[str] = None
    in_stock: Optional[bool] = None
    is_default: Optional[bool] = None


class ProductCard(BaseModel):
    """Canonical product-card contract shared by sync and streaming responses."""
    id: Optional[str] = None
    sku: Optional[str] = None
    product_group_id: Optional[str] = None
    product_id: Optional[str] = None
    handle: Optional[str] = None
    name: str
    price_minor: Optional[int] = None
    price: Optional[int] = None  # Legacy input compatibility only.
    price_unit: Literal["minor"] = "minor"
    currency: Optional[str] = None
    currency_source: Optional[CurrencySource] = None
    category: Optional[str] = None
    in_stock: Optional[bool] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    description: Optional[str] = None
    has_variants: Optional[bool] = None
    variant_count: Optional[int] = None
    default_variant_id: Optional[str] = None
    variants: List[ProductVariant] = Field(default_factory=list)


class CommerceMetadata(BaseModel):
    cart: Optional[CommerceCart] = None
    validated_product_ids: List[str] = Field(default_factory=list)


class MessageResponse(BaseModel):
    """Response model for message processing."""
    message: str
    conversation_id: str
    citations: List[Citation] = []
    products: List[Dict[str, Any]] = []
    dealers: List[Dict[str, Any]] = []
    metadata: Optional[Dict[str, Any]] = None
    commerce: Optional[CommerceMetadata] = None
    context_used: int = 0
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class StreamingMessageResponse(BaseModel):
    """Response model for streaming messages."""
    type: str = Field(..., description="Type of chunk: 'status', 'content', 'metadata', 'error'")
    content: str = ""
    conversation_id: str
    citations: List[Citation] = []
    context_used: Optional[int] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    products: Optional[List[Dict[str, Any]]] = None  # Phase 5: Product cards
    dealers: Optional[List[Dict[str, Any]]] = None   # Phase 5: Dealer cards
    metadata: Optional[Dict[str, Any]] = None
    commerce: Optional[CommerceMetadata] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class IngestionResponse(BaseModel):
    """Response model for ingestion operations."""
    success: bool
    chunk_id: Optional[str] = None
    message: str
    chunks_created: Optional[int] = None
    processing_time_ms: Optional[int] = None


class IngestionStatus(BaseModel):
    """Status model for ingestion jobs."""
    job_id: str
    status: str = Field(..., description="Status: 'pending', 'processing', 'completed', 'error', 'cancelled'")
    files_count: int = 0
    processed_count: int = 0
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
