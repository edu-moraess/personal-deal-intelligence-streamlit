"""End-to-end search pipeline: parser → provider → matching → history → ranking."""
from __future__ import annotations
from typing import Optional
from src.domain.matching import is_compatible
from src.domain.models import Condition, Offer, ProviderResult, ProviderStatus
from src.domain.parser import parse_natural_query
from src.domain.pricing import attach_history_to_offer
from src.persistence.repository import Repository
from src.providers.base import Provider
from src.providers.mercadolivre import MercadoLivreProvider

class SearchPipeline:
    def __init__(self, providers: Optional[list[Provider]] = None, repository: Optional[Repository] = None):
        self.providers = providers or [MercadoLivreProvider()]
        self.repo = repository or Repository()
    def run(self, raw_query: str, max_price: Optional[float] = None, condition: Condition = Condition.NEW) -> dict:
        query=parse_natural_query(raw_query, explicit_max_price=max_price, condition=condition)
        all_offers: list[Offer]=[]
        provider_statuses=[]
        for provider in self.providers:
            result: ProviderResult=provider.search(query)
            provider_statuses.append({"provider":result.provider,"status":result.status.value,"message":result.message,"count":len(result.offers)})
            if result.status != ProviderStatus.AVAILABLE: continue
            for offer in result.offers:
                self.repo.save_offer_snapshot(offer)
                attach_history_to_offer(offer, self.repo.get_history_for_product(offer.provider, offer.external_id))
                all_offers.append(offer)
        all_offers.sort(key=lambda o:(0 if o.match_level.value=="EXACT_MATCH" else 1,o.effective_price if o.effective_price is not None else 1e12,0 if o.free_shipping else 1))
        compatible=[o for o in all_offers if is_compatible(o.match_level)]
        self.repo.log_search(raw_query, query.to_dict(), len(compatible), self.providers[0].name if self.providers else "none")
        return {"normalized":query.to_dict(),"offers":[o.to_display_dict() for o in compatible],"provider_statuses":provider_statuses,"result_count":len(compatible)}
