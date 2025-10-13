"""
Integration tests for MessageService with Phase 5 memory system.

Tests the complete flow:
1. User message storage in short-term
2. Safety escalation checking
3. Semantic retrieval
4. Memory context building
5. LLM response generation
6. Assistant message storage
7. Episodic fact extraction
8. Auto-summary triggering
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.message_service import MessageService
from app.schemas.message import MessageRequest, MessageRole
from retrieval.types import RetrievalContext, RetrievalChunk
from llm.types import LLMResponse
from memory.types import MemoryFact, Escalation, EscalationSeverity, GraphRule


@pytest.fixture
def mock_settings():
    """Mock application settings."""
    with patch("app.services.message_service.settings") as mock_settings:
        mock_settings.MONGODB_URI = "mongodb://localhost:27017"
        mock_settings.MONGODB_DATABASE = "test_db"
        mock_settings.OPENAI_API_KEY = "test_key"
        yield mock_settings


@pytest.fixture
def mock_mongo_client():
    """Mock MongoDB async client."""
    with patch("app.services.message_service.AsyncIOMotorClient") as mock_client:
        mock_db = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        yield mock_client


@pytest.fixture
def mock_retrieval_pipeline():
    """Mock retrieval pipeline."""
    with patch("app.services.message_service.RetrievalPipeline") as mock_pipeline:
        mock_instance = AsyncMock()
        mock_pipeline.return_value = mock_instance
        
        # Mock retrieve method
        mock_instance.retrieve.return_value = RetrievalContext(
            query="test query",
            chunks=[
                RetrievalChunk(
                    doc_id="doc1",
                    content="Sample product information",
                    title="Product Manual",
                    url="https://example.com/manual",
                    score=0.95,
                    metadata={"category": "manual"}
                )
            ],
            metadata={"total_results": 1}
        )
        
        yield mock_instance


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider."""
    with patch("app.services.message_service.llm") as mock_llm:
        mock_factory = MagicMock()
        mock_llm.factory.create_provider.return_value = mock_factory
        
        # Mock generate method
        async def mock_generate(prompt, **kwargs):
            return LLMResponse(
                text="This is a helpful response with citations.",
                model="gpt-4o-mini",
                usage={"prompt_tokens": 100, "completion_tokens": 50}
            )
        
        mock_factory.generate = mock_generate
        
        yield mock_factory


@pytest.fixture
def mock_memory_components():
    """Mock all Phase 5 memory components."""
    with patch("app.services.message_service.ShortTermMemory") as mock_short, \
         patch("app.services.message_service.EpisodicMemory") as mock_episodic, \
         patch("app.services.message_service.GraphMemory") as mock_graph:
        
        # Mock short-term memory
        mock_short_instance = AsyncMock()
        mock_short.return_value = mock_short_instance
        mock_short_instance.add_message = AsyncMock()
        mock_short_instance.get_recent_messages.return_value = []
        mock_short_instance.should_summarize.return_value = False
        mock_short_instance.summaries = MagicMock()
        mock_short_instance.summaries.find.return_value.sort.return_value.to_list = AsyncMock(return_value=[])
        
        # Mock episodic memory
        mock_episodic_instance = AsyncMock()
        mock_episodic.return_value = mock_episodic_instance
        mock_episodic_instance.get_user_facts.return_value = [
            MemoryFact(
                user_id="user123",
                fact="User prefers email communication",
                confidence=0.85,
                context={"source": "conversation"},
                timestamp=datetime.now(),
                ttl=90
            )
        ]
        mock_episodic_instance.extract_and_store_facts = AsyncMock()
        
        # Mock graph memory
        mock_graph_instance = AsyncMock()
        mock_graph.return_value = mock_graph_instance
        mock_graph_instance.check_escalation.return_value = []
        mock_graph_instance.match_rules.return_value = [
            GraphRule(
                brand_id="brand123",
                name="Warranty Policy",
                conditions={"topic": "warranty"},
                action={"type": "provide_info", "message": "Our warranty covers 2 years"},
                priority=1
            )
        ]
        
        yield {
            "short_term": mock_short_instance,
            "episodic": mock_episodic_instance,
            "graph": mock_graph_instance
        }


@pytest.mark.asyncio
async def test_process_message_basic_flow(
    mock_settings,
    mock_mongo_client,
    mock_retrieval_pipeline,
    mock_llm_provider,
    mock_memory_components
):
    """Test basic message processing with Phase 5 memory."""
    
    # Create service
    service = MessageService()
    
    # Override memory components with mocks
    service.short_term = mock_memory_components["short_term"]
    service.episodic = mock_memory_components["episodic"]
    service.graph = mock_memory_components["graph"]
    service.retrieval_pipeline = mock_retrieval_pipeline
    service.llm_provider = mock_llm_provider
    
    # Create request
    request = MessageRequest(
        message="What is the warranty on this product?",
        user_id="user123",
        brand_id="brand123",
        conversation_id="conv123",
        page_context={"url": "https://example.com/product"}
    )
    
    # Process message
    response = await service.process_message(request)
    
    # Verify steps
    assert response is not None
    assert response.message == "This is a helpful response with citations."
    
    # Verify user message stored
    mock_memory_components["short_term"].add_message.assert_any_call(
        conversation_id="conv123",
        role=MessageRole.USER,
        content="What is the warranty on this product?",
        metadata={"user_id": "user123"}
    )
    
    # Verify escalation checked
    mock_memory_components["graph"].check_escalation.assert_called_once()
    
    # Verify retrieval called
    mock_retrieval_pipeline.retrieve.assert_called_once()
    
    # Verify facts extracted
    mock_memory_components["episodic"].extract_and_store_facts.assert_called_once()
    
    # Verify assistant message stored
    assert mock_memory_components["short_term"].add_message.call_count == 2  # User + Assistant


@pytest.mark.asyncio
async def test_process_message_with_escalation(
    mock_settings,
    mock_mongo_client,
    mock_retrieval_pipeline,
    mock_llm_provider,
    mock_memory_components
):
    """Test message processing with safety escalation."""
    
    # Setup escalation
    escalation = Escalation(
        brand_id="brand123",
        trigger_keywords=["gas", "smell"],
        severity=EscalationSeverity.CRITICAL,
        action={"type": "escalate_emergency", "message": "Call emergency services immediately"}
    )
    mock_memory_components["graph"].check_escalation.return_value = [escalation]
    
    # Create service
    service = MessageService()
    service.short_term = mock_memory_components["short_term"]
    service.episodic = mock_memory_components["episodic"]
    service.graph = mock_memory_components["graph"]
    service.retrieval_pipeline = mock_retrieval_pipeline
    service.llm_provider = mock_llm_provider
    
    # Create request with safety trigger
    request = MessageRequest(
        message="I smell gas coming from the heater",
        user_id="user123",
        brand_id="brand123",
        conversation_id="conv123"
    )
    
    # Process message
    response = await service.process_message(request)
    
    # Verify escalation was checked
    mock_memory_components["graph"].check_escalation.assert_called_once()
    
    # Verify response still generated (but should include safety warning)
    assert response is not None


@pytest.mark.asyncio
async def test_process_message_auto_summary_trigger(
    mock_settings,
    mock_mongo_client,
    mock_retrieval_pipeline,
    mock_llm_provider,
    mock_memory_components
):
    """Test auto-summary triggering after 4 turns."""
    
    # Setup should_summarize to return True
    mock_memory_components["short_term"].should_summarize.return_value = True
    mock_memory_components["short_term"].trigger_summary = AsyncMock()
    
    # Create service
    service = MessageService()
    service.short_term = mock_memory_components["short_term"]
    service.episodic = mock_memory_components["episodic"]
    service.graph = mock_memory_components["graph"]
    service.retrieval_pipeline = mock_retrieval_pipeline
    service.llm_provider = mock_llm_provider
    
    # Create request
    request = MessageRequest(
        message="Fourth message in conversation",
        user_id="user123",
        brand_id="brand123",
        conversation_id="conv123"
    )
    
    # Process message
    response = await service.process_message(request)
    
    # Verify summary was triggered
    mock_memory_components["short_term"].should_summarize.assert_called_once()
    mock_memory_components["short_term"].trigger_summary.assert_called_once()


@pytest.mark.asyncio
async def test_stream_message_basic_flow(
    mock_settings,
    mock_mongo_client,
    mock_retrieval_pipeline,
    mock_llm_provider,
    mock_memory_components
):
    """Test streaming message processing."""
    
    # Create service
    service = MessageService()
    service.short_term = mock_memory_components["short_term"]
    service.episodic = mock_memory_components["episodic"]
    service.graph = mock_memory_components["graph"]
    service.retrieval_pipeline = mock_retrieval_pipeline
    service.llm_provider = mock_llm_provider
    
    # Mock streaming response
    async def mock_stream_generate(prompt, **kwargs):
        chunks = ["This ", "is ", "a ", "streaming ", "response."]
        for chunk in chunks:
            yield chunk
    
    service.llm_provider.stream_generate = mock_stream_generate
    
    # Create request
    request = MessageRequest(
        message="Tell me about the product",
        user_id="user123",
        brand_id="brand123",
        conversation_id="conv123"
    )
    
    # Stream message
    chunks = []
    async for chunk in service.stream_message(request):
        chunks.append(chunk)
    
    # Verify we got status updates and content
    assert len(chunks) > 0
    
    # Check for different message types
    message_types = [chunk.type for chunk in chunks]
    assert "status" in message_types  # Status updates
    assert "content" in message_types  # Response content
    
    # Verify memory operations were called
    assert mock_memory_components["short_term"].add_message.call_count >= 2


@pytest.mark.asyncio
async def test_build_memory_context(
    mock_settings,
    mock_mongo_client,
    mock_memory_components
):
    """Test memory context building."""
    
    # Create service
    service = MessageService()
    service.short_term = mock_memory_components["short_term"]
    service.episodic = mock_memory_components["episodic"]
    service.graph = mock_memory_components["graph"]
    
    # Build context
    context = await service._build_memory_context(
        user_id="user123",
        brand_id="brand123",
        conversation_id="conv123",
        query="test query",
        escalations=[]
    )
    
    # Verify structure
    assert "recent_messages" in context
    assert "user_facts" in context
    assert "matched_rules" in context
    assert "escalations" in context
    assert "summaries" in context
    
    # Verify memory calls
    mock_memory_components["short_term"].get_recent_messages.assert_called_once()
    mock_memory_components["episodic"].get_user_facts.assert_called_once()
    mock_memory_components["graph"].match_rules.assert_called_once()


@pytest.mark.asyncio
async def test_build_prompt_with_full_context(
    mock_settings,
    mock_mongo_client,
    mock_memory_components
):
    """Test prompt building with all memory layers."""
    
    # Create service
    service = MessageService()
    
    # Create mock retrieval context
    retrieval_context = RetrievalContext(
        query="test",
        chunks=[
            RetrievalChunk(
                doc_id="doc1",
                content="Product information",
                title="Manual",
                url="https://example.com",
                score=0.9,
                metadata={}
            )
        ],
        metadata={}
    )
    
    # Create mock memory context
    memory_context = {
        "recent_messages": [],
        "user_facts": [
            MemoryFact(
                user_id="user123",
                fact="Prefers email",
                confidence=0.8,
                context={},
                timestamp=datetime.now(),
                ttl=90
            )
        ],
        "matched_rules": [
            GraphRule(
                brand_id="brand123",
                name="Warranty",
                conditions={},
                action={"message": "2 year warranty"},
                priority=1
            )
        ],
        "escalations": [],
        "summaries": []
    }
    
    # Build prompt
    prompt = service._build_prompt(
        message="What is the warranty?",
        retrieval_context=retrieval_context,
        memory_context=memory_context,
        escalations=[]
    )
    
    # Verify prompt contains all elements
    assert "Product information" in prompt  # KB context
    assert "Prefers email" in prompt  # User facts
    assert "Warranty" in prompt  # Rules
    assert "What is the warranty?" in prompt  # Current message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
