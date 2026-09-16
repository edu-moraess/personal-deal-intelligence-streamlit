from datetime import datetime, timedelta
from src.domain.models import PriceObservation
from src.domain.pricing import calculate_effective_price, compute_history_stats

def test_effective_price():
    assert calculate_effective_price(3799, None) == 3799.0
    assert calculate_effective_price(3799, 49.9) == 3848.9
    assert calculate_effective_price(3999, 0, confirmed_coupon=200, confirmed_cashback=100) == 3699.0

def test_history_requires_real_observations():
    now=datetime.utcnow()
    obs=[PriceObservation("ml:1","Mercado Livre","Mercado Livre",3700,0,3700,now-timedelta(days=10)),PriceObservation("ml:1","Mercado Livre","Mercado Livre",3900,0,3900,now-timedelta(days=5)),PriceObservation("ml:1","Mercado Livre","Mercado Livre",3800,0,3800,now-timedelta(days=1))]
    stats=compute_history_stats(obs, now=now)
    assert stats["sufficient"] is True
    assert stats["min_30d"] == 3700.0
    assert stats["min_7d"] == 3800.0
