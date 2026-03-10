"""
Quality Loop Module

Provides iterative quality improvement with score-based evaluation.
Inspired by Reflex Loop from ai-factory.
"""

__version__ = "0.1.0"

from specify_cli.quality.loop import QualityLoop
from specify_cli.quality.rules import RuleManager
from specify_cli.quality.evaluator import Evaluator
from specify_cli.quality.scorer import Scorer
from specify_cli.quality.critique import Critique
from specify_cli.quality.refiner import Refiner

__all__ = [
    "QualityLoop",
    "RuleManager",
    "Evaluator",
    "Scorer",
    "Critique",
    "Refiner",
]
