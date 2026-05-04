"""
Goal System — Autonomous strategic goal proposal, voting, and persistence.

Goals are proposed by Metis (the strategic planning agent), flow through
MAKER consensus voting, and are persisted via :class:`FileGoalStore` using
atomic file writes.
"""

from .models import Goal, Vote
from .store import FileGoalStore

__all__ = [
    "FileGoalStore",
    "Goal",
    "Vote",
]
