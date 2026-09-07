"""Quantiacs Q25 strategy factory: desks, ideas, render, gates, evolve, runner."""

from .ideas import Idea, SEED_IDEAS
from .gates import GateResult, evaluate_hard_gates, evaluate_soft_gates
from .registry import Registry

__all__ = [
    "Idea",
    "SEED_IDEAS",
    "GateResult",
    "evaluate_hard_gates",
    "evaluate_soft_gates",
    "Registry",
]

__version__ = "0.1.0"
