"""Observer Node - Extracts insights for long-term memory"""

import logging
from typing import Dict, Any
from datetime import datetime

from langgraph.runtime import Runtime

from ..state import SoporteState
from ..context import SoporteContext

logger = logging.getLogger(__name__)


async def observer_node(state: SoporteState, runtime: Runtime[SoporteContext]) -> Dict[str, Any]:
    """Extract insights from conversation for long-term memory

    This node:
    1. Analyzes the conversation messages
    2. Extracts preferences and recurring issues
    3. Stores insights in PostgreSQL Store (namespace: motoboy_{id})

    Args:
        state: Current graph state
        config: Runtime configuration

    Returns:
        Dict with state updates (resets should_observe flag)
    """
    try:
        ctx = runtime.context
        config = runtime.config
        motoboy_id = config["configurable"]["motoboy_id"]

        # Skip if observer is disabled or conversation is too short
        if not ctx.enable_observer or len(state.messages) < 4:
            return {"should_observe": False}

        logger.info(f"observer_node: extracting insights for motoboy {motoboy_id}")

        # TODO: Implement insight extraction
        # 1. Use LLM with structured output to extract:
        #    - User preferences
        #    - Recurring issues
        #    - Important context for future conversations
        # 2. Store in PostgreSQL Store:
        #    namespace = ("motoboy", str(motoboy_id), "preferences")
        #    namespace = ("motoboy", str(motoboy_id), "recurring_issues")

        logger.warning("observer_node not yet fully implemented")

        return {"should_observe": False}

    except Exception as e:
        logger.error(f"Error in observer_node: {e}", exc_info=True)
        return {"should_observe": False}
