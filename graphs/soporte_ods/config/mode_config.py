"""MODE configuration for Soporte ODS - Production, Staging, Evaluation"""

import os
from typing import Dict, Any


# MODE definitions
# 1 = Production
# 2 = Staging
# 3 = Evaluation (mock data)

MODE_CONFIGS: Dict[int, Dict[str, Any]] = {
    1: {  # Production
        "name": "production",
        "db_url": os.getenv("PROD_DB_URL"),
        "firebase_creds_path": "graphs/soporte_ods/config/prod_firebase.json",
        "api_base_url": os.getenv("PROD_API_BASE_URL", "https://api.pedidosya.com"),
        "use_mock_data": False,
    },
    2: {  # Staging
        "name": "staging",
        "db_url": os.getenv("STAGING_DB_URL"),
        "firebase_creds_path": "graphs/soporte_ods/config/staging_firebase.json",
        "api_base_url": os.getenv("STAGING_API_BASE_URL", "https://staging-api.pedidosya.com"),
        "use_mock_data": False,
    },
    3: {  # Evaluation (mock data for testing)
        "name": "evaluation",
        "db_url": None,
        "firebase_creds_path": None,
        "api_base_url": None,
        "use_mock_data": True,
    },
}


def get_mode_config(mode: int) -> Dict[str, Any]:
    """Get configuration for a specific MODE

    Args:
        mode: MODE number (1=prod, 2=staging, 3=eval)

    Returns:
        Configuration dictionary for the specified mode

    Raises:
        ValueError: If mode is not valid
    """
    if mode not in MODE_CONFIGS:
        raise ValueError(f"Invalid MODE: {mode}. Must be 1 (prod), 2 (staging), or 3 (eval)")

    return MODE_CONFIGS[mode]
