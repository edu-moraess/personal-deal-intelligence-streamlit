"""Mercado Livre official public search API provider. No scraping or synthetic data."""
from __future__ import annotations
import os
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlencode
import requests
from src.domain.matching import is_compatible, match_offer
from src.domain.models import Condition, MatchLevel, NormalizedQuery, Offer, ProviderResult, ProviderStatus
from src.domain.pricing import calculate_effective_price
from src.providers.base import Provider

ML_BASE = "https://api.mercadolibre.com/sites/MLB/search"
DEFAULT_TIMEOUT = 8.0

class MercadoLivreProvider(Provider):
    name = "Mercado Livre"
    def __init__(self, timeout: float = DEFAULT_TIMEOUT, access_token: Optional[str] = None):
        self.timeout = timeout
        self.access_token = access_token or os.getenv("ML_ACCESS_TOKEN")
    def search(self, query: NormalizedQuery) -> ProviderResult:
        params: dict[str, Any] = {"q": query.clean_query, "limit": 50}
        if query.condition != Condition.ALL: params["condition"] = query.condition.value
        headers = {"Accept":"application/json","User-Agent":"PersonalDealIntelligence/1.0"}
        if self.access_token: headers["Authorization"] = f"Bearer {self.access_token}"
        retrieved_at = datetime.utcnow()
        try:
            resp = requests.get(f"{ML_BASE}?{urlencode(params)}", headers=headers, timeout=self.timeout)
        except requests.Timeout:
            return ProviderResult(self.name, ProviderStatus.UNAVAILABLE, [], "Timeout ao consultar Mercado Livre.", retrieved_at)
        except requests.RequestException as exc:
            return ProviderResult(self.name, ProviderStatus.ERROR, [], f"Erro de rede: {exc.__class__.__name__}", retrieved_at)
        if resp.status_code == 401: return ProviderResult(self.name, ProviderStatus.AUTH_REQUIRED, [], "Autenticação necessária ou token inválido.", retrieved_at)
        if resp.status_code == 403: return ProviderResult(self.name, ProviderStatus.UNAVAILABLE, [], "Mercado Livre — indisponível no momento (403).", retrieved_at)
        if resp.status_code == 429: return ProviderResult(self.name, ProviderStatus.RATE_LIMITED, [], "Limite de requisições atingido (429).", retrieved_at)
        if resp.status_code >= 500: return ProviderResult(self.name, ProviderStatus.ERROR, [], f"Erro do servidor Mercado Livre ({resp.status_code}).", retrieved_at)
        if not resp.ok: return ProviderResult(self.name, ProviderStatus.ERROR, [], f"Resposta inesperada ({resp.status_code}).", retrieved_at)
        try: payload = resp.json()
        except ValueError: return ProviderResult(self.name, ProviderStatus.ERROR, [], "Resposta inválida (JSON).", retrieved_at)
        offers=[]
        for item in payload.get("results") or []:
            offer=self._map_item(item, query, retrieved_at)
            if offer is None or not is_compatible(offer.match_level): continue
            if query.max_price is not None and offer.effective_price is not None and offer.effective_price > query.max_price: continue
            offers.append(offer)
        offers.sort(key=lambda o:(0 if o.match_level==MatchLevel.EXACT_MATCH else 1,o.effective_price if o.effective_price is not None else 1e12,0 if o.free_shipping else 1))
        return ProviderResult(self.name, ProviderStatus.AVAILABLE, offers[:24], None, retrieved_at)
    def _map_item(self, item: dict[str, Any], query: NormalizedQuery, retrieved_at: datetime) -> Optional[Offer]:
        title=item.get("title") or ""
        if not title: return None
        try: price=float(item.get("price") or 0)
        except (TypeError,ValueError): return None
        if price <= 0: return None
        original=item.get("original_price")
        original_price=float(original) if isinstance(original,(int,float)) and original>price else None
        shipping_info=item.get("shipping") or {}
        free_shipping=bool(shipping_info.get("free_shipping"))
        shipping_cost=shipping_info.get("cost")
        shipping=float(shipping_cost) if isinstance(shipping_cost,(int,float)) and shipping_cost>=0 else None
        condition=Condition.USED if (item.get("condition") or "new").lower()=="used" else Condition.NEW
        thumbnail=item.get("thumbnail") or item.get("thumbnail_id")
        if isinstance(thumbnail,str) and thumbnail.startswith("http"):
            image_url=thumbnail.replace("-I.jpg","-O.jpg").replace("-I.web","-O.web")
        else: image_url=thumbnail if isinstance(thumbnail,str) else None
        return Offer(external_id=str(item.get("id","")),title=title,price=price,original_price=original_price,shipping=shipping,free_shipping=free_shipping,permalink=item.get("permalink") or "",image_url=image_url,store=self.name,provider=self.name,condition=condition,match_level=match_offer(title,query),effective_price=calculate_effective_price(price,shipping),retrieved_at=retrieved_at)
