"""Domain models for Personal Deal Intelligence."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

class MatchLevel(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    HIGH_MATCH = "HIGH_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    INVALID_MATCH = "INVALID_MATCH"

class ProviderStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    ERROR = "ERROR"

class Condition(str, Enum):
    NEW = "new"
    USED = "used"
    ALL = "all"

@dataclass(frozen=True)
class NormalizedQuery:
    raw: str
    clean_query: str
    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    storage: Optional[str] = None
    size: Optional[str] = None
    refresh_rate: Optional[str] = None
    gpu_model: Optional[str] = None
    max_price: Optional[float] = None
    condition: Condition = Condition.NEW
    required_terms: tuple[str, ...] = field(default_factory=tuple)
    strict_matching: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw, "clean_query": self.clean_query, "category": self.category,
            "brand": self.brand, "model": self.model, "storage": self.storage,
            "size": self.size, "refresh_rate": self.refresh_rate, "gpu_model": self.gpu_model,
            "max_price": self.max_price, "condition": self.condition.value,
            "required_terms": list(self.required_terms), "strict_matching": self.strict_matching,
        }

@dataclass
class ProductIdentity:
    title: str
    brand: Optional[str] = None
    model: Optional[str] = None
    gtin: Optional[str] = None
    sku: Optional[str] = None
    mpn: Optional[str] = None
    storage: Optional[str] = None
    size: Optional[str] = None
    refresh_rate: Optional[str] = None
    gpu_model: Optional[str] = None
    attributes: dict[str, str] = field(default_factory=dict)

@dataclass
class Offer:
    external_id: str
    title: str
    price: float
    original_price: Optional[float]
    shipping: Optional[float]
    free_shipping: bool
    permalink: str
    image_url: Optional[str]
    store: str
    provider: str
    condition: Condition
    match_level: MatchLevel
    effective_price: Optional[float]
    retrieved_at: datetime
    identity: Optional[ProductIdentity] = None
    history_summary: Optional[str] = None
    history_stats: Optional[dict[str, Any]] = None

    def to_display_dict(self) -> dict[str, Any]:
        return {
            "external_id": self.external_id, "title": self.title, "price": self.price,
            "original_price": self.original_price, "shipping": self.shipping,
            "free_shipping": self.free_shipping, "permalink": self.permalink,
            "image_url": self.image_url, "store": self.store, "provider": self.provider,
            "condition": self.condition.value, "match_level": self.match_level.value,
            "effective_price": self.effective_price, "retrieved_at": self.retrieved_at.isoformat(),
            "history_summary": self.history_summary, "history_stats": self.history_stats,
        }

@dataclass
class ProviderResult:
    provider: str
    status: ProviderStatus
    offers: list[Offer]
    message: Optional[str] = None
    retrieved_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class PriceObservation:
    product_key: str
    provider: str
    store: str
    price: float
    shipping: Optional[float]
    effective_price: float
    captured_at: datetime
    title: Optional[str] = None
    image_url: Optional[str] = None
    permalink: Optional[str] = None
