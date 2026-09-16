"""Structured product matching: mandatory attributes before text coverage."""
from __future__ import annotations
import re
import unicodedata
from typing import Optional
from .models import MatchLevel, NormalizedQuery, ProductIdentity

def _clean(text: str) -> str:
    text = text.lower().strip().replace("”", '"').replace("“", '"').replace("″", '"').replace("'", '"')
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r'[^a-z0-9.+"\s]+', " ", text)).strip()

def _extract_storage(title: str) -> Optional[str]:
    matches = list(re.finditer(r"\b(\d+)\s*(gb|tb)\b", _clean(title), re.IGNORECASE))
    if not matches: return None
    m = matches[-1]
    return f"{m.group(1)}{m.group(2).upper()}"

def _extract_size(title: str) -> Optional[str]:
    t = _clean(title)
    m = re.search(r'(?:^|\s)(\d{1,2}(?:\.\d)?)\s*(?:polegadas?|polegada|"|\'\'|pol)(?=\s|$)', t)
    if m: return m.group(1)
    m = re.search(r'\b(\d{1,2}(?:\.\d)?)"', t)
    return m.group(1) if m else None

def _extract_refresh(title: str) -> Optional[str]:
    m = re.search(r"\b(\d{2,3})\s*hz\b", _clean(title), re.IGNORECASE)
    return m.group(1) if m else None

def _extract_gpu(title: str) -> Optional[str]:
    m = re.search(r"\b(?:rtx|gtx|rx)\s*\d{3,4}(?:\s*(?:ti|xt|super))?\b", _clean(title), re.IGNORECASE)
    return m.group(0).upper() if m else None

def build_identity_from_title(title: str, brand: Optional[str] = None) -> ProductIdentity:
    return ProductIdentity(title=title, brand=brand, storage=_extract_storage(title), size=_extract_size(title), refresh_rate=_extract_refresh(title), gpu_model=_extract_gpu(title))

def match_offer(title: str, query: NormalizedQuery) -> MatchLevel:
    if not title or not title.strip(): return MatchLevel.INVALID_MATCH
    t = _clean(title)
    q_model = _clean(query.model) if query.model else None
    if query.storage:
        title_storage = _extract_storage(title)
        if title_storage is None or title_storage.upper() != query.storage.upper(): return MatchLevel.INVALID_MATCH
    if query.size:
        title_size = _extract_size(title)
        if title_size is None or title_size != query.size: return MatchLevel.INVALID_MATCH
    if query.refresh_rate:
        title_rr = _extract_refresh(title)
        if title_rr is None or title_rr != query.refresh_rate: return MatchLevel.INVALID_MATCH
    if query.gpu_model:
        title_gpu = _extract_gpu(title)
        if title_gpu is None or query.gpu_model.upper().strip() != title_gpu.upper().strip(): return MatchLevel.INVALID_MATCH
    if q_model:
        variant_markers = ["ultra","plus","+","pro max","pro+","fe","lite","mini","max"]
        q_has_variant = any(v in q_model for v in variant_markers)
        t_has_variant = any(v in t for v in variant_markers)
        if not q_has_variant and t_has_variant:
            base = re.sub(r"\s*(ultra|plus|\+|pro max|fe|lite|mini|max)\s*", " ", q_model).strip()
            if base and base in t: return MatchLevel.INVALID_MATCH
        if q_has_variant:
            for v in variant_markers:
                if v in q_model and v not in t: return MatchLevel.INVALID_MATCH
        core_tokens = [tok for tok in q_model.split() if tok not in ("galaxy","iphone")]
        if core_tokens and not all(tok in t for tok in core_tokens):
            model_num = re.search(r"[a-z]?\d{1,3}", q_model)
            if model_num and model_num.group(0) not in t: return MatchLevel.INVALID_MATCH
    required = list(query.required_terms) or [tok for tok in _clean(query.clean_query).split() if len(tok)>1]
    hits = sum(1 for term in required if _clean(term) in t)
    coverage = hits / (len(required) or 1)
    if coverage >= .99: return MatchLevel.EXACT_MATCH
    if coverage >= .7: return MatchLevel.HIGH_MATCH
    if coverage >= .4: return MatchLevel.PARTIAL_MATCH
    return MatchLevel.INVALID_MATCH

def is_compatible(level: MatchLevel) -> bool:
    return level in (MatchLevel.EXACT_MATCH, MatchLevel.HIGH_MATCH)
