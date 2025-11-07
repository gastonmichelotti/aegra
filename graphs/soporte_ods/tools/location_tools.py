"""Location Tools - Tools for fetching motoboy location from Firebase"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


async def get_motoboy_location(
    motoboy_id: int,
    mode: int = 1,
) -> Dict[str, Any]:
    """Obtener ubicación en tiempo real del motoboy desde Firebase

    Args:
        motoboy_id: ID del motoboy
        mode: MODE de ejecución (1=prod, 2=staging, 3=eval)

    Returns:
        Dict con:
        {
            "latitude": float,
            "longitude": float,
            "timestamp": datetime,
            "accuracy": float (opcional)
        }

    Example:
        >>> location = await get_motoboy_location(12345)
        >>> print(f"Lat: {location['latitude']}, Lng: {location['longitude']}")
    """
    # TODO: Implement Firebase integration
    # Different Firebase projects for prod/staging
    # MODE 3 returns mock location

    logger.warning("get_motoboy_location not yet fully implemented")

    # Return mock data for now
    import random
    from datetime import datetime

    random.seed(motoboy_id)

    return {
        "latitude": random.uniform(-34.7056, -34.5265),
        "longitude": random.uniform(-58.5315, -58.3314),
        "timestamp": datetime.now(),
        "accuracy": random.uniform(5.0, 20.0),
        "_mock": True,
        "_note": "TODO: Implement Firebase integration"
    }
