"""Runtime context for Soporte ODS graph"""

from dataclasses import dataclass
from typing import Dict, Any

from .config.mode_config import get_mode_config


@dataclass
class SoporteContext:
    """Runtime context for Soporte ODS graph

    This context is passed to all nodes via LangGraph's runtime context pattern.
    It includes:
    - mode: Execution mode (1=prod, 2=staging, 3=eval)
    - model: LLM model to use
    - temperature: LLM temperature
    - context_refresh_minutes: How often to refresh pre-computed context
    - enable_observer: Whether to run the observer node for long-term memory

    Note: motoboy_id is now in the State, not in Context. Pass it in the input once.
    The context automatically loads MODE-specific configuration via mode_config property.
    """

    # Execution mode (1=prod, 2=staging, 3=eval)
    mode: int = 1

    # LLM configuration
    model: str = "openai/gpt-4-turbo"
    temperature: float = 0.3

    # Context refresh interval (minutes)
    # How often to re-fetch motoboy, viaje, reserva, location data
    context_refresh_minutes: int = 5

    # Observer configuration
    # Whether to run the observer node for long-term memory extraction
    enable_observer: bool = True

    @property
    def mode_config(self) -> Dict[str, Any]:
        """Get MODE-specific configuration

        Returns configuration for the current mode including:
        - db_url: Database connection URL
        - api_base_url: Base URL for external APIs
        - firebase_creds_path: Path to Firebase credentials
        - use_mock_data: Whether to use mock data (MODE 3 only)

        Returns:
            Dict with MODE-specific configuration
        """
        return get_mode_config(self.mode)

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.mode == 1

    @property
    def is_staging(self) -> bool:
        """Check if running in staging mode"""
        return self.mode == 2

    @property
    def is_evaluation(self) -> bool:
        """Check if running in evaluation mode (mock data)"""
        return self.mode == 3
