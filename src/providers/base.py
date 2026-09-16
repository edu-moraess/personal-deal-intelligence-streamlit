"""Provider interface."""
from __future__ import annotations
from abc import ABC, abstractmethod
from src.domain.models import NormalizedQuery, ProviderResult

class Provider(ABC):
    name: str = "Unknown"
    @abstractmethod
    def search(self, query: NormalizedQuery) -> ProviderResult:
        ...
