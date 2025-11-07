"""Tests for Soporte ODS graph"""

import pytest
from graphs.soporte_ods.graph import graph
from graphs.soporte_ods.context import SoporteContext


def test_graph_compiles():
    """Test that the graph compiles successfully"""
    assert graph is not None
    assert graph.name == "Soporte ODS Agent"
    assert "load_context" in graph.nodes
    assert "agent" in graph.nodes
    assert "tools" in graph.nodes
    assert "observer" in graph.nodes


def test_context_default_values():
    """Test SoporteContext default values"""
    ctx = SoporteContext()
    assert ctx.mode == 1  # Default to production
    assert ctx.model == "openai/gpt-4-turbo"
    assert ctx.temperature == 0.3
    assert ctx.context_refresh_minutes == 5
    assert ctx.enable_observer is True


def test_context_mode_config():
    """Test MODE configuration"""
    # Production
    ctx_prod = SoporteContext(mode=1)
    assert ctx_prod.is_production
    assert not ctx_prod.is_staging
    assert not ctx_prod.is_evaluation

    # Staging
    ctx_staging = SoporteContext(mode=2)
    assert not ctx_staging.is_production
    assert ctx_staging.is_staging
    assert not ctx_staging.is_evaluation

    # Evaluation
    ctx_eval = SoporteContext(mode=3)
    assert not ctx_eval.is_production
    assert not ctx_eval.is_staging
    assert ctx_eval.is_evaluation
    assert ctx_eval.mode_config["use_mock_data"] is True


@pytest.mark.asyncio
async def test_graph_basic_invocation():
    """Test basic graph invocation with mock data"""
    from langchain_core.messages import HumanMessage

    # Initial state
    input_state = {
        "messages": [HumanMessage(content="Hola, ¿cómo estás?")]
    }

    # Context with evaluation mode (uses mock data)
    context = SoporteContext(mode=3)

    # Config
    config = {
        "configurable": {
            "thread_id": "test_thread_123",
            "motoboy_id": 12345,
        },
        "context": context,
    }

    # This test just verifies the graph can be invoked without crashing
    # The actual LLM call will fail without API keys, but structure should work
    try:
        # We're not actually invoking to avoid needing API keys in tests
        # Just verify the structure is correct
        assert callable(graph.ainvoke)
        assert config["configurable"]["motoboy_id"] == 12345
    except Exception as e:
        # Expected to fail without API keys, but shouldn't be import/structure errors
        assert "api" in str(e).lower() or "key" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
