"""Natural language purchase-query parser."""
from __future__ import annotations
import re
import unicodedata
from typing import Optional
from .models import Condition, NormalizedQuery

STOP_WORDS = {
    "ate","por","menos","maximo","max","r$","rs","para","com","sem","de","da","do","das","dos",
    "e","ou","um","uma","o","a","os","as","em","no","na","novo","nova","lacrado","programacao",
    "masculino","feminino","polegadas","polegada","hz","gb","tb","cm","mm",
}
KNOWN_BRANDS = [
    "Samsung","Apple","iPhone","Xiaomi","Motorola","LG","Sony","Asus","Lenovo","Dell","Acer",
    "NVIDIA","AMD","Intel","Kingston","Logitech","JBL","Philips","Huawei","Realme","Poco","OnePlus","Google",
]

def _clean(text: str) -> str:
    text = text.lower().strip().replace("”", '"').replace("“", '"').replace("″", '"')
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r'[^a-z0-9."\s]+', " ", text)
    return re.sub(r"\s+", " ", text).strip()

def _title_case(value: Optional[str]) -> Optional[str]:
    return " ".join(w.capitalize() for w in value.split()) if value else None

def parse_natural_query(raw: str, explicit_max_price: Optional[float] = None, condition: Condition = Condition.NEW) -> NormalizedQuery:
    if not raw or not raw.strip():
        raise ValueError("Query cannot be empty")
    raw = raw.strip()
    price_pattern = r"(?:até|ate|max(?:imo)?|por\s+menos\s+de|no\s+máximo|no\s+maximo)\s*(?:r\$\s*)?([\d.]+(?:,[\d]{1,2})?)"
    price_match = re.search(price_pattern, raw, re.IGNORECASE)
    max_price = explicit_max_price
    if max_price is None and price_match:
        try:
            max_price = float(price_match.group(1).replace(".", "").replace(",", "."))
        except ValueError:
            pass
    without_price = re.sub(price_pattern, "", raw, flags=re.IGNORECASE).strip()
    normalized = _clean(re.sub(r"\s+", " ", without_price))

    capacity_matches = list(re.finditer(r"\b(\d+)\s*(gb|tb)\b", normalized, re.IGNORECASE))
    storage = None
    if capacity_matches:
        m = capacity_matches[-1]
        storage = f"{m.group(1)}{m.group(2).upper()}"

    size_match = re.search(r'(?:^|\s)(\d{1,2}(?:\.\d)?)\s*(?:polegadas?|polegada|"|\'\'|pol)(?=\s|$)', normalized)
    size = size_match.group(1) if size_match else None
    refresh_match = re.search(r"\b(\d{2,3})\s*hz\b", normalized, re.IGNORECASE)
    refresh_rate = refresh_match.group(1) if refresh_match else None

    gpu_match = re.search(r"\b(?:rtx|gtx|rx)\s*\d{3,4}(?:\s*(?:ti|xt|super))?\b", normalized, re.IGNORECASE)
    gpu_model = gpu_match.group(0).upper().replace("  ", " ") if gpu_match else None
    if gpu_model:
        storage = None

    brand = None
    for candidate in KNOWN_BRANDS:
        if _clean(candidate) in normalized:
            brand = candidate
            break
    if "iphone" in normalized and brand is None:
        brand = "Apple"

    category = None
    if "monitor" in normalized:
        category = "Monitor"
    elif any(t in normalized for t in ("notebook","laptop","ultrabook")):
        category = "Notebook"
    elif any(t in normalized for t in ("iphone","galaxy","celular","smartphone","xiaomi","motorola")):
        category = "Smartphone"
    elif any(t in normalized for t in ("rtx","gtx","rx","gpu","placa de video","placa de vídeo")):
        category = "GPU"
    elif any(t in normalized for t in ("tenis","tênis","sneaker")):
        category = "Calçados"

    model = None
    if gpu_model:
        model = gpu_model
    elif brand == "Apple" or "iphone" in normalized:
        m = re.search(r"iphone\s+\d+(?:\s+(?:pro|plus|max|mini))*(?:\s+max)?", normalized)
        if m: model = _title_case(m.group(0))
    elif brand == "Samsung" or "galaxy" in normalized:
        m = re.search(r"(?:galaxy\s+)?([a-z]?\d{1,3}(?:\s*(?:fe|ultra|plus|\+|lite|pro))?)", normalized, re.IGNORECASE)
        if m:
            raw_model = m.group(0).strip()
            if not raw_model.lower().startswith("galaxy"):
                raw_model = "Galaxy " + raw_model
            model = _title_case(raw_model)
    elif brand:
        parts = normalized.split()
        try:
            idx = next(i for i,p in enumerate(parts) if _clean(brand) in p)
            candidates = parts[idx+1:idx+4]
            model_tokens = [t for t in candidates if t not in STOP_WORDS and not re.match(r"^\d+$", t)]
            if model_tokens: model = _title_case(" ".join(model_tokens[:2]))
        except StopIteration:
            pass

    tokens = [t for t in normalized.split() if len(t)>1 and t not in STOP_WORDS and not re.match(r"^\d+$", t)]
    required = list(dict.fromkeys(tokens))
    if storage and storage.lower() not in required:
        required.append(storage.lower())
    if gpu_model:
        required = [t for t in gpu_model.lower().split() if t]

    return NormalizedQuery(
        raw=raw, clean_query=without_price or raw, category=category, brand=brand, model=model,
        storage=storage, size=size, refresh_rate=refresh_rate, gpu_model=gpu_model,
        max_price=max_price, condition=condition, required_terms=tuple(required), strict_matching=True,
    )
