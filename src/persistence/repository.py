"""Repository for products, real price history and watchlist."""
from __future__ import annotations
import json
from datetime import datetime
from typing import Any, Optional
from src.domain.models import Offer, PriceObservation
from src.persistence.db import init_db, session

class Repository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(db_path)
    def log_search(self, raw_query: str, normalized: dict[str, Any], result_count: int, provider: str) -> None:
        with session(self.db_path) as conn:
            conn.execute("INSERT INTO searches (raw_query, normalized_json, result_count, provider) VALUES (?, ?, ?, ?)", (raw_query, json.dumps(normalized, ensure_ascii=False), result_count, provider))
    def save_offer_snapshot(self, offer: Offer) -> Optional[int]:
        if offer.effective_price is None: return None
        with session(self.db_path) as conn:
            conn.execute("""
                INSERT INTO products (provider, external_id, title, image_url, source_url, updated_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(provider, external_id) DO UPDATE SET title=excluded.title, image_url=excluded.image_url, source_url=excluded.source_url, updated_at=datetime('now')
            """, (offer.provider, offer.external_id, offer.title, offer.image_url, offer.permalink))
            row = conn.execute("SELECT id FROM products WHERE provider=? AND external_id=?", (offer.provider, offer.external_id)).fetchone()
            if not row: return None
            product_id = row["id"]
            recent = conn.execute("SELECT effective_price,captured_at FROM price_history WHERE product_id=? ORDER BY captured_at DESC LIMIT 1", (product_id,)).fetchone()
            should_insert = True
            if recent:
                try:
                    last = datetime.fromisoformat(recent["captured_at"])
                    same_price = abs(float(recent["effective_price"])-float(offer.effective_price)) < .005
                    within_hour = (offer.retrieved_at-last).total_seconds() < 3600
                    should_insert = not (same_price and within_hour)
                except (TypeError, ValueError):
                    pass
            if should_insert:
                conn.execute("INSERT INTO price_history (product_id,provider,store,price,shipping,effective_price,captured_at) VALUES (?,?,?,?,?,?,?)", (product_id,offer.provider,offer.store,offer.price,offer.shipping,offer.effective_price,offer.retrieved_at.isoformat()))
            return product_id
    def get_history_for_product(self, provider: str, external_id: str) -> list[PriceObservation]:
        with session(self.db_path) as conn:
            rows = conn.execute("SELECT h.*,p.title,p.image_url,p.source_url FROM price_history h JOIN products p ON p.id=h.product_id WHERE p.provider=? AND p.external_id=? ORDER BY h.captured_at ASC", (provider, external_id)).fetchall()
        out=[]
        for r in rows:
            out.append(PriceObservation(product_key=f"{provider}:{external_id}", provider=r["provider"], store=r["store"], price=float(r["price"]), shipping=float(r["shipping"]) if r["shipping"] is not None else None, effective_price=float(r["effective_price"]), captured_at=datetime.fromisoformat(r["captured_at"]), title=r["title"], image_url=r["image_url"], permalink=r["source_url"]))
        return out
    def list_watchlist(self) -> list[dict[str, Any]]:
        with session(self.db_path) as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM watchlist ORDER BY created_at DESC").fetchall()]
    def add_watchlist(self, query: str, target_price: Optional[float] = None, maximum_price: Optional[float] = None) -> dict[str, Any]:
        with session(self.db_path) as conn:
            conn.execute("INSERT INTO watchlist (query,target_price,maximum_price) VALUES (?,?,?) ON CONFLICT(query) DO UPDATE SET target_price=excluded.target_price, maximum_price=excluded.maximum_price", (query,target_price,maximum_price))
            row=conn.execute("SELECT * FROM watchlist WHERE query=?", (query,)).fetchone()
        return dict(row) if row else {"query":query,"target_price":target_price}
    def remove_watchlist(self, item_id: int) -> None:
        with session(self.db_path) as conn:
            conn.execute("DELETE FROM watchlist WHERE id=?", (item_id,))
