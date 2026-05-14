from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class Profile:
    name: str = "Athlete"
    age: int = 28


@dataclass
class WeightEntry:
    entry_date: date
    weight_lb: float
