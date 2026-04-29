import asyncio

import pytest

from retrieval.pipeline import RetrievalPipeline
from retrieval.types import DocumentChunk, RetrievalConfig, SearchResult


class FakeSearch:
    def __init__(self, name, events):
        self.name = name
        self.events = events

    async def search(self, query, **_kwargs):
        self.events.append(f"{self.name}:start")
        await asyncio.sleep(0.01)
        self.events.append(f"{self.name}:end")
        return SearchResult(
            chunks=[
                DocumentChunk(
                    chunk_id=f"{self.name}-chunk",
                    doc_id=f"{self.name}-doc",
                    content=f"{self.name} result for {query}",
                    score=1.0,
                )
            ],
            total_found=1,
            query=query,
            search_type=self.name,
        )


class FakeFusion:
    def fuse(self, search_results, top_k):
        chunks = []
        for result in search_results:
            chunks.extend(result.chunks)
        return chunks[:top_k]


@pytest.mark.asyncio
async def test_retrieval_runs_vector_and_bm25_concurrently():
    events = []
    pipeline = RetrievalPipeline.__new__(RetrievalPipeline)
    pipeline.config = RetrievalConfig(
        vector_enabled=True,
        bm25_enabled=True,
        vector_top_k=10,
        bm25_top_k=10,
        rerank_enabled=False,
        dedup_enabled=False,
        brand_boost_enabled=False,
        page_boost_enabled=False,
    )
    pipeline.vector_search = FakeSearch("vector", events)
    pipeline.bm25_search = FakeSearch("bm25", events)
    pipeline.rrf = FakeFusion()
    pipeline.reranker = None
    pipeline.brand_boost = None
    pipeline.page_boost = None

    result = await pipeline.retrieve("pillar cock", max_chunks=10)

    assert len(result.chunks) == 2
    assert events.index("bm25:start") < events.index("vector:end")
