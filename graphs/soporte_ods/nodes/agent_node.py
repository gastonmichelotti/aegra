"""Agent Node - Main LLM node with all tools"""

import logging
from typing import Dict, Any, cast

from langchain_core.messages import AIMessage
from langgraph.runtime import Runtime

from ..state import SoporteState
from ..context import SoporteContext
from ..tools import TOOLS
from ..prompts import build_system_prompt
from ..utils import load_chat_model

logger = logging.getLogger(__name__)


async def agent_node(state: SoporteState, runtime: Runtime[SoporteContext]) -> Dict[str, Any]:
    """Main agent node with LLM + tools

    This node:
    1. Builds system prompt with current context
    2. Calls LLM with all available tools
    3. Returns updates to state (messages, should_observe flag)

    Args:
        state: Current graph state
        runtime: Runtime context with configuration

    Returns:
        Dict with state updates
    """
    try:
        ctx = runtime.context

        # Build system prompt with context
        system_prompt = build_system_prompt(
            motoboy=state.motoboy,
            viaje=state.viaje,
            reserva=state.reserva,
            location=state.location_info,
        )

        logger.info(f"agent_node: model={ctx.model}, temperature={ctx.temperature}")

        # Initialize model with tool binding and temperature
        model = load_chat_model(ctx.model).bind_tools(TOOLS)
        if ctx.temperature is not None:
            model = model.bind(temperature=ctx.temperature)

        # Call LLM with system prompt + conversation history
        response = cast(
            AIMessage,
            await model.ainvoke(
                [{"role": "system", "content": system_prompt}, *state.messages]
            ),
        )

        # Handle last step edge case
        if state.is_last_step and response.tool_calls:
            return {
                "messages": [
                    AIMessage(
                        id=response.id,
                        content="Disculpa, no pude completar tu consulta en el número de pasos permitido. Por favor, intenta reformular tu pregunta o usa `derive_to_human` para contactar a un agente.",
                    )
                ],
                "should_observe": False,
            }

        # Determine if we should observe (conversation ending without tool calls)
        should_observe = ctx.enable_observer and not response.tool_calls

        logger.info(f"agent_node: response generated, tool_calls={len(response.tool_calls or [])}, should_observe={should_observe}")

        return {
            "messages": [response],
            "should_observe": should_observe,
        }

    except Exception as e:
        logger.error(f"Error in agent_node: {e}", exc_info=True)
        # Return error message to user
        return {
            "messages": [
                AIMessage(
                    content=f"Disculpa, ocurrió un error al procesar tu mensaje: {str(e)}. Por favor, intenta de nuevo."
                )
            ],
            "should_observe": False,
        }
