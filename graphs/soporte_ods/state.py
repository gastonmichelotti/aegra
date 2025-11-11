"""State definition for Soporte ODS graph"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Optional, Sequence, List

from langgraph.graph.message import add_messages, AnyMessage
from langgraph.managed import IsLastStep

from .models import MotoboyModel, ViajeModel, ReservaModel


@dataclass
class SoporteState:
    """State for Soporte ODS ReactAgent graph

    This state includes:
    - messages: Conversation history (managed by LangGraph)
    - motoboy_id: ID of the motoboy (set once at initialization)
    - Context data: Pre-computed domain models (motoboy, viaje, reserva, location)
    - Confirmation flow: Pending confirmations for state-changing operations
    - Observer flag: Whether to run long-term memory extraction
    - Framework fields: is_last_step for recursion control
    """

    # Core conversation messages
    messages: Annotated[Sequence[AnyMessage], add_messages]

    # Motoboy ID - set once at initialization, persisted in checkpoints
    motoboy_id: Optional[int] = None

    # Pre-computed context data - DOMAIN MODEL CLASSES (not dicts)
    # These are fetched once and cached in checkpoints, refreshed periodically
    motoboy: Optional[MotoboyModel] = None
    viaje: Optional[ViajeModel | List[ViajeModel]] = None
    reserva: Optional[ReservaModel] = None
    location_info: Optional[dict] = None  # Firebase location data (keep as dict)

    # Context refresh tracking
    last_context_refresh: Optional[datetime] = None

    # Confirmation flow state
    # Used by api_tools to track pending confirmations for state-changing operations
    pending_confirmation: Optional[dict] = None

    # Long-term memory observer flag
    # Set to True to trigger the observer node for insights extraction
    should_observe: bool = False

    # Framework-managed recursion control
    is_last_step: IsLastStep = field(default_factory=lambda: IsLastStep(False))
