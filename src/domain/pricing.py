"""Price intelligence based exclusively on real observations."""
from __future__ import annotations
from datetime import datetime, timedelta
from statistics import median
from typing import Any, Optional, Sequence
from .models import Offer, PriceObservation

def calculate_effective_price(price: float, shipping: Optional[float] = None, confirmed_coupon: Optional[float] = None, confirmed_cashback: Optional[float] = None) -> float:
    total = float(price)
    if shipping is not None and shipping > 0: total += float(shipping)
    if confirmed_coupon is not None and confirmed_coupon > 0: total -= float(confirmed_coupon)
    if confirmed_cashback is not None and confirmed_cashback > 0: total -= float(confirmed_cashback)
    return round(max(total, 0.0), 2)

def compute_history_stats(observations: Sequence[PriceObservation], now: Optional[datetime] = None) -> dict[str, Any]:
    now = now or datetime.utcnow()
    if not observations:
        return {"count":0,"sufficient":False,"message":"Histórico insuficiente","min_all":None,"max_all":None,"avg_all":None,"median_all":None,"min_7d":None,"min_30d":None,"min_90d":None,"avg_30d":None,"median_30d":None}
    prices = [o.effective_price for o in observations]
    def window(days: int) -> list[float]:
        cutoff = now - timedelta(days=days)
        return [o.effective_price for o in observations if o.captured_at >= cutoff]
    p7,p30,p90 = window(7),window(30),window(90)
    sufficient = len(p30) >= 2 or len(p90) >= 3
    def safe_min(v): return round(min(v),2) if v else None
    def safe_avg(v): return round(sum(v)/len(v),2) if v else None
    def safe_med(v): return round(float(median(v)),2) if v else None
    stats = {"count":len(prices),"sufficient":sufficient,"min_all":safe_min(prices),"max_all":round(max(prices),2),"avg_all":safe_avg(prices),"median_all":safe_med(prices),"min_7d":safe_min(p7),"min_30d":safe_min(p30),"min_90d":safe_min(p90),"avg_30d":safe_avg(p30),"median_30d":safe_med(p30)}
    if not sufficient:
        stats["message"] = "Histórico insuficiente"
    else:
        parts=[]
        if stats["min_30d"] is not None: parts.append(f"Mínimo 30d: R$ {stats['min_30d']:,.2f}".replace(",","X").replace(".",",").replace("X","."))
        if stats["avg_30d"] is not None: parts.append(f"Média 30d: R$ {stats['avg_30d']:,.2f}".replace(",","X").replace(".",",").replace("X","."))
        stats["message"] = " · ".join(parts) if parts else "Dados históricos disponíveis"
    return stats

def classify_price_position(current: Optional[float], stats: dict[str, Any]) -> str:
    if current is None or not stats.get("sufficient"): return "Histórico insuficiente"
    avg = stats.get("avg_30d") or stats.get("avg_all")
    if avg is None: return "Histórico insuficiente"
    if current < avg*.97: return "Abaixo da média histórica"
    if current > avg*1.03: return "Acima da média"
    return "Próximo da média"

def attach_history_to_offer(offer: Offer, observations: Sequence[PriceObservation]) -> Offer:
    stats = compute_history_stats(observations)
    offer.history_stats = stats
    offer.history_summary = stats["message"]
    return offer
