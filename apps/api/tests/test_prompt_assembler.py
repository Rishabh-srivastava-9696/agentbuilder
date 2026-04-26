from app.services.prompt_assembler import PromptAssembler


def test_prompt_assembler_normalizes_legacy_agent_fields():
    assembler = PromptAssembler()
    agent = {
        "name": "Essco",
        "description": "Bathware assistant",
        "brand_slug": "essco-bathware",
        "system_prompt": "You are the Essco assistant.",
        "metadata": {
            "purpose": "Answer product and dealer questions",
            "role": "Sales assistant",
        },
    }
    config = {
        "personality": {
            "traits": ["clear", "helpful"],
            "communication_style": "concise",
            "response_format": "short paragraphs",
        },
        "security": {
            "rate_limiting": True,
            "content_filtering": True,
            "session_timeout": 30,
            "max_conversation_length": 50,
        },
        "features": {"human_takeover": True},
        "data_source": "rag",
        "rag": {"enabled": True, "retrieval": {"top_k": 5}},
    }

    assembly = assembler.assemble_agent_prompt(agent, config)

    assert assembly.prompt_version == "layers:v1"
    assert len(assembly.cacheable_prefix_hash) == 16
    assert "Platform System Contract" in assembly.prompt
    assert "Agent Identity / SOUL.md" in assembly.prompt
    assert "You are the Essco assistant." in assembly.prompt
    assert "Agent Duties / DUTIES.md" in assembly.prompt
    assert "essco-bathware" in assembly.prompt
    assert "Behavior Rules / RULES.md" in assembly.prompt
    assert "Data Source Policy / knowledge/index.yaml" in assembly.prompt


def test_prompt_assembler_prefers_explicit_prompt_layers_and_runtime_variables():
    assembler = PromptAssembler()
    agent = {
        "name": "Legacy name",
        "description": "Legacy description",
        "system_prompt": "Legacy prompt",
    }
    config = {
        "prompt_layers": {
            "version": "layers:v1",
            "soul": "Fixed SOUL text",
            "duties": {"name": "Layered agent", "role": "Support"},
            "rules": {"unsupported_claims": "Escalate"},
            "data_source_policy": {"default_sources": ["products"]},
            "runtime_variables_schema": {
                "page_context": {"allowed_fields": ["url", "title"]},
                "filters": {"source": "request"},
            },
        }
    }

    assembly = assembler.assemble_agent_prompt(agent, config)
    runtime_context = assembler.build_runtime_context(
        config=config,
        page_context={
            "url": "https://example.com/products",
            "title": "Products",
            "metadata": {"collection": "faucets"},
        },
        filters={"category": "faucets"},
    )

    assert "Fixed SOUL text" in assembly.prompt
    assert "Legacy prompt" not in assembly.prompt
    assert runtime_context["runtime_variables_schema"]["page_context"]["allowed_fields"] == ["url", "title"]
    assert runtime_context["data_source_policy"]["default_sources"] == ["products"]
    assert runtime_context["page_context"]["url"] == "https://example.com/products"
    assert runtime_context["page_context"]["metadata"]["collection"] == "faucets"
    assert runtime_context["filters"] == {"category": "faucets"}


def test_prompt_hash_changes_only_when_stable_layers_change():
    assembler = PromptAssembler()
    agent = {"name": "Essco", "description": "Assistant", "system_prompt": "Stable prompt"}
    config = {"prompt_layers": {"soul": "Stable prompt", "rules": {"grounding": "strict"}}}

    first = assembler.assemble_agent_prompt(agent, config)
    second = assembler.assemble_agent_prompt(agent, config)
    changed = assembler.assemble_agent_prompt(
        agent,
        {"prompt_layers": {"soul": "Stable prompt", "rules": {"grounding": "relaxed"}}},
    )

    assert first.cacheable_prefix_hash == second.cacheable_prefix_hash
    assert first.cacheable_prefix_hash != changed.cacheable_prefix_hash
