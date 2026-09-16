"""
Personal Deal Intelligence — Streamlit MVP

Ferramenta pessoal de inteligência de compras.
Precisão > quantidade. Zero dados fictícios.
"""

from __future__ import annotations

import html
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.domain.models import Condition
from src.persistence.repository import Repository
from src.providers.mercadolivre import MercadoLivreProvider
from src.services.search_pipeline import SearchPipeline

st.set_page_config(
    page_title="Personal Deal Intelligence",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.stApp { background-color: #F7F8FA; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1100px; }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
h1 { font-weight: 600; letter-spacing: -0.02em; color: #172033; margin-bottom: 0.25rem; }
.subtitle { color: #667085; font-size: 0.95rem; margin-bottom: 1.5rem; }
.stTextInput > div > div > input { border-radius: 8px; border: 1px solid #D0D5DD; padding: 0.75rem 1rem; font-size: 1rem; background: #FFFFFF; color: #172033; }
.offer-card { background:#FFFFFF; border:1px solid #E4E7EC; border-radius:12px; padding:1.1rem; margin-bottom:1rem; display:flex; flex-direction:column; gap:.75rem; height:100%; box-shadow: 0 1px 2px rgba(16,24,40,.04); }
.offer-image { width:100%; aspect-ratio:1; object-fit:contain; background:#F2F4F7; border-radius:8px; max-height:180px; }
.offer-image-placeholder { width:100%; aspect-ratio:1; background:#F2F4F7; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#98A2B3; font-size:.8rem; max-height:180px; }
.offer-title { font-size:.95rem; font-weight:600; color:#172033; line-height:1.35; margin:0; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.offer-store { font-size:.8rem; color:#667085; margin:0; }
.offer-price { font-size:1.25rem; font-weight:700; color:#172033; margin:0; }
.offer-original { font-size:.8rem; color:#98A2B3; text-decoration:line-through; }
.offer-shipping { font-size:.8rem; color:#475467; }
.offer-effective { font-size:.85rem; color:#344054; font-weight:500; }
.match-exact,.match-high { display:inline-block; font-size:.72rem; font-weight:600; padding:.2rem .5rem; border-radius:4px; }
.match-exact { color:#175CD3; background:#EFF8FF; }
.match-high { color:#344054; background:#F2F4F7; }
.history-line { font-size:.78rem; color:#667085; line-height:1.4; }
.status-unavailable { background:#FFFAEB; border:1px solid #FEDF89; border-radius:8px; padding:.9rem 1.1rem; color:#7A2E0E; font-size:.9rem; margin-bottom:1rem; }
.empty-state { text-align:center; padding:2.5rem 1rem; color:#667085; }
a.offer-link { display:inline-block; margin-top:.4rem; font-size:.85rem; font-weight:600; color:#175CD3; text-decoration:none; }
a.offer-link:hover { text-decoration:underline; }
.stButton > button { border-radius: 8px; border: 1px solid #175CD3; background: #175CD3; color: #FFFFFF; font-weight: 600; }
.stButton > button:hover { background: #1849A9; border-color: #1849A9; color: #FFFFFF; }
</style>
""", unsafe_allow_html=True)


def get_secret(name: str) -> str | None:
    """Read a Streamlit secret first, then an environment variable."""
    try:
        value = st.secrets.get(name)
        if value:
            return str(value).strip()
    except Exception:
        pass
    value = os.getenv(name)
    return value.strip() if value else None


def build_pipeline() -> SearchPipeline:
    token = get_secret("ML_ACCESS_TOKEN")
    return SearchPipeline(providers=[MercadoLivreProvider(access_token=token)])


def fmt_brl(value: float | None) -> str:
    if value is None:
        return "Não informado"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def match_label(level: str) -> str:
    if level == "EXACT_MATCH":
        return '<span class="match-exact">Correspondência exata</span>'
    if level == "HIGH_MATCH":
        return '<span class="match-high">Alta correspondência</span>'
    return html.escape(level)


def render_offer_card(offer: dict) -> None:
    image_url = offer.get("image_url")
    image_html = (
        f'<img src="{html.escape(str(image_url), quote=True)}" class="offer-image" alt="" loading="lazy" />'
        if image_url
        else '<div class="offer-image-placeholder">Imagem não fornecida</div>'
    )
    original_html = ""
    if offer.get("original_price") and offer["original_price"] > offer["price"]:
        original_html = f'<div class="offer-original">De {fmt_brl(offer["original_price"])}</div>'
    if offer.get("free_shipping"):
        shipping_txt = "Frete grátis"
    elif offer.get("shipping") is not None:
        shipping_txt = f"+ {fmt_brl(offer['shipping'])} de frete"
    else:
        shipping_txt = "Frete não informado"
    history = offer.get("history_summary") or "Histórico insuficiente"
    stats = offer.get("history_stats") or {}
    if stats.get("sufficient"):
        parts = []
        if stats.get("min_30d") is not None:
            parts.append(f"Mín. 30d: {fmt_brl(stats['min_30d'])}")
        if stats.get("avg_30d") is not None:
            parts.append(f"Média 30d: {fmt_brl(stats['avg_30d'])}")
        if stats.get("count"):
            parts.append(f"{stats['count']} obs.")
        history = " · ".join(parts) if parts else history
    condition = "Novo" if offer.get("condition") == "new" else "Usado"
    title = html.escape(str(offer.get("title", "")))
    store = html.escape(str(offer.get("store", "")))
    permalink = html.escape(str(offer.get("permalink", "#")), quote=True)
    st.markdown(f"""
    <div class="offer-card">
        {image_html}
        <p class="offer-title">{title}</p>
        <p class="offer-store">{store} · {condition}</p>
        {original_html}
        <p class="offer-price">{fmt_brl(offer.get("price"))}</p>
        <div class="offer-shipping">{shipping_txt}</div>
        <div class="offer-effective">Preço efetivo: {fmt_brl(offer.get("effective_price"))}</div>
        <div>{match_label(offer.get("match_level", ""))}</div>
        <div class="history-line">{html.escape(str(history))}</div>
        <a class="offer-link" href="{permalink}" target="_blank" rel="noopener noreferrer">Ver oferta</a>
    </div>
    """, unsafe_allow_html=True)


if "pipeline" not in st.session_state:
    st.session_state.pipeline = build_pipeline()
if "last_result" not in st.session_state:
    st.session_state.last_result = None

st.markdown("# Personal Deal Intelligence")
st.markdown('<p class="subtitle">Ferramenta pessoal de busca precisa e inteligência de preços. Sem anúncios.</p>', unsafe_allow_html=True)

with st.form("search_form", clear_on_submit=False):
    query = st.text_input(
        "O que você está procurando?",
        value="Samsung Galaxy S25 256GB até R$ 4.000",
        placeholder="Ex.: RTX 5070 12GB até R$ 4.000",
        label_visibility="visible",
    )
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        max_price_str = st.text_input("Preço máximo (opcional)", value="", placeholder="4000")
    with col2:
        condition_label = st.selectbox("Condição", ["Novo", "Usado", "Todos"], index=0)
    with col3:
        st.write("")
        st.write("")
        submitted = st.form_submit_button("Buscar", use_container_width=True)

condition_map = {"Novo": Condition.NEW, "Usado": Condition.USED, "Todos": Condition.ALL}
condition = condition_map[condition_label]

max_price = None
if max_price_str.strip():
    try:
        max_price = float(max_price_str.replace(".", "").replace(",", "."))
    except ValueError:
        st.warning("Preço máximo inválido; a busca seguirá sem esse filtro.")

if submitted:
    if not query or len(query.strip()) < 2:
        st.warning("Descreva o produto que você procura.")
    else:
        with st.spinner("Consultando fontes reais..."):
            try:
                st.session_state.last_result = st.session_state.pipeline.run(
                    raw_query=query.strip(), max_price=max_price, condition=condition
                )
            except Exception as exc:
                st.error(f"Erro inesperado na busca: {exc}")
                st.session_state.last_result = None

result = st.session_state.last_result
if result is not None:
    for ps in result.get("provider_statuses", []):
        if ps.get("status") != "AVAILABLE":
            msg = ps.get("message") or f"{ps.get('provider')} — indisponível no momento"
            st.markdown(f'<div class="status-unavailable"><strong>{html.escape(str(ps.get("provider", "Fonte")))}</strong><br>{html.escape(str(msg))}</div>', unsafe_allow_html=True)

    offers = result.get("offers") or []
    normalized = result.get("normalized") or {}
    st.markdown(f"### {len(offers)} oferta{'s' if len(offers) != 1 else ''} compatível{'is' if len(offers) != 1 else ''}")
    chips = []
    for key in ("brand", "model", "storage"):
        if normalized.get(key):
            chips.append(normalized[key])
    if normalized.get("size"):
        chips.append(f'{normalized["size"]}"')
    if normalized.get("refresh_rate"):
        chips.append(f'{normalized["refresh_rate"]}Hz')
    if normalized.get("max_price"):
        chips.append(f'até {fmt_brl(normalized["max_price"])}')
    if chips:
        st.caption("Entendido como: " + " · ".join(str(c) for c in chips))

    if not offers:
        any_unavailable = any(ps.get("status") != "AVAILABLE" for ps in result.get("provider_statuses", []))
        if any_unavailable:
            st.info("Nenhuma fonte retornou resultados utilizáveis no momento.")
        else:
            st.markdown('<div class="empty-state"><strong>Nenhuma correspondência rigorosa encontrada</strong><br>Produtos que não atendem aos atributos obrigatórios são excluídos.</div>', unsafe_allow_html=True)
    else:
        cols = st.columns(3)
        for idx, offer in enumerate(offers):
            with cols[idx % 3]:
                render_offer_card(offer)

st.divider()
with st.expander("Minha lista (watchlist)", expanded=False):
    repo: Repository = st.session_state.pipeline.repo
    items = repo.list_watchlist()
    if not items:
        st.caption("Nenhum item salvo ainda.")
    else:
        for item in items:
            c1, c2 = st.columns([5, 1])
            with c1:
                target = fmt_brl(item.get("target_price")) if item.get("target_price") else "—"
                st.write(f"**{item['query']}** · Meta: {target}")
            with c2:
                if st.button("Remover", key=f"rm_{item['id']}"):
                    repo.remove_watchlist(item["id"])
                    st.rerun()
    add_q = st.text_input("Salvar busca atual na lista", key="wl_query", value=query if "query" in dir() else "")
    add_target = st.text_input("Preço-alvo (opcional)", key="wl_target")
    if st.button("Adicionar à lista"):
        t_price = None
        if add_target.strip():
            try:
                t_price = float(add_target.replace(".", "").replace(",", "."))
            except ValueError:
                pass
        if add_q.strip():
            repo.add_watchlist(add_q.strip(), target_price=t_price, maximum_price=t_price)
            st.success("Salvo.")
            st.rerun()
