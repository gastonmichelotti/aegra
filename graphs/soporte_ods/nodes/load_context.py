"""Load Context Node - Pre-computes motoboy, viaje, reserva, and location data"""

import logging
from datetime import datetime
from typing import Dict, Any

from langgraph.runtime import Runtime

from ..state import SoporteState
from ..context import SoporteContext
from ..services import MotoboyService, ViajeService, ReservaService
from ..tools.location_tools import get_motoboy_location

logger = logging.getLogger(__name__)


async def load_context_node(state: SoporteState, runtime: Runtime[SoporteContext]) -> Dict[str, Any]:
    """Load/refresh pre-computed context data

    This node:
    1. Checks if context needs refresh (based on last_context_refresh timestamp)
    2. If needed, fetches fresh data for: motoboy, viaje, reserva, location
    3. Returns updates to state with the refreshed data

    The context is cached in checkpoints and only refreshed when:
    - It's the first time (last_context_refresh is None)
    - Enough time has passed since last refresh (based on context_refresh_minutes)

    Args:
        state: Current graph state
        config: Runtime configuration (contains motoboy_id)

    Returns:
        Dict with state updates (motoboy, viaje, reserva, location_info, last_context_refresh)
    """
    try:
        # Get runtime context and config
        ctx = runtime.context
        config = runtime.config
        motoboy_id = config["configurable"]["motoboy_id"]
        mode = ctx.mode

        logger.info(f"load_context_node: motoboy_id={motoboy_id}, mode={mode}")

        # Check if refresh is needed
        needs_refresh = _should_refresh_context(state, ctx)

        if not needs_refresh:
            logger.info("Context is fresh, skipping refresh")
            return {}  # No updates needed, use cached state

        logger.info(f"Refreshing context (mode={mode})")

        # Fetch all context data in parallel for efficiency
        import asyncio

        motoboy_result, viaje_result, reserva_result, location_info = await asyncio.gather(
            MotoboyService.get_by_id(motoboy_id, mode),
            ViajeService.get_by_id_motoboy(motoboy_id, mode),
            ReservaService.get_by_id_motoboy(motoboy_id, mode),
            get_motoboy_location(motoboy_id, mode),
            return_exceptions=True  # Don't fail if one fetch fails
        )

        # Build state updates
        updates = {
            "last_context_refresh": datetime.now(),
        }

        # Update motoboy if successful
        if not isinstance(motoboy_result, Exception) and motoboy_result.get("success"):
            updates["motoboy"] = motoboy_result["data"]
            logger.info("✓ Motoboy context loaded")
        else:
            logger.warning(f"Failed to load motoboy: {motoboy_result}")

        # Update viaje if successful
        if not isinstance(viaje_result, Exception) and viaje_result.get("success"):
            updates["viaje"] = viaje_result["data"]
            logger.info("✓ Viaje context loaded")
        else:
            logger.warning(f"Failed to load viaje: {viaje_result}")

        # Update reserva if successful
        if not isinstance(reserva_result, Exception) and reserva_result.get("success"):
            updates["reserva"] = reserva_result["data"]
            logger.info("✓ Reserva context loaded")
        else:
            logger.warning(f"Failed to load reserva: {reserva_result}")

        # Update location if successful
        if not isinstance(location_info, Exception):
            updates["location_info"] = location_info
            logger.info("✓ Location context loaded")
        else:
            logger.warning(f"Failed to load location: {location_info}")

        return updates

    except Exception as e:
        logger.error(f"Error in load_context_node: {e}", exc_info=True)
        # Return empty dict to avoid breaking the graph
        # The agent will work with whatever context is already in state
        return {}


def _should_refresh_context(state: SoporteState, ctx: SoporteContext) -> bool:
    """Check if context needs to be refreshed

    Args:
        state: Current graph state
        ctx: Runtime context with refresh settings

    Returns:
        bool: True if context should be refreshed
    """
    # First run - always refresh
    if state.last_context_refresh is None:
        return True

    # Check time since last refresh
    time_since_refresh = datetime.now() - state.last_context_refresh
    refresh_threshold_seconds = ctx.context_refresh_minutes * 60

    return time_since_refresh.total_seconds() > refresh_threshold_seconds
