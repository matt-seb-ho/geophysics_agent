#!/usr/bin/env python3
"""
ChromaDB Explorer — browse and query all GEOS RAG collections.

Usage:
    uv run streamlit run scripts/db_explorer.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import chromadb
import streamlit as st
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from src.geos_agent.constants import (
    COLLECTION_NAVIGATOR,
    COLLECTION_SCHEMA,
    COLLECTION_TECHNICAL,
    VECTOR_DB_DIR,
)

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GEOS DB Explorer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ─────────────────────────────────────────────────────────────────

COLLECTIONS = {
    "geos_navigator":  {"label": "Navigator",  "emoji": "🗺️",  "color": "#4361ee"},
    "geos_technical":  {"label": "Technical",  "emoji": "⚙️",  "color": "#2ec4b6"},
    "geos_schema":     {"label": "Schema",     "emoji": "📐",  "color": "#ff9f1c"},
}

# ── Cached resources ──────────────────────────────────────────────────────────

@st.cache_resource
def get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=str(VECTOR_DB_DIR))


@st.cache_resource
def get_embedding_fn():
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        api_base="https://openrouter.ai/api/v1",
        model_name="qwen/qwen3-embedding-8b",
    )


@st.cache_resource
def get_collection(name: str):
    client = get_client()
    emb = get_embedding_fn()
    try:
        return client.get_collection(name=name, embedding_function=emb)
    except Exception:
        return None


def collection_count(name: str) -> int:
    col = get_collection(name)
    return col.count() if col else 0


# ── Helpers ───────────────────────────────────────────────────────────────────

def render_navigator_result(meta: dict, doc: str, dist: float | None = None):
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**{meta.get('title', 'No title')}**")
            if bc := meta.get("breadcrumbs"):
                st.caption(bc)
        with c2:
            if dist is not None:
                score = round(1 - dist, 3)
                color = "#2ec4b6" if score > 0.7 else "#ff9f1c" if score > 0.4 else "#e71d36"
                st.markdown(
                    f"<span style='color:{color};font-weight:bold;font-size:1.1em'>▶ {score:.3f}</span>",
                    unsafe_allow_html=True,
                )
        cols = st.columns(3)
        cols[0].caption(f"type: `{meta.get('chunk_type','?')}`")
        cols[1].caption(f"source: `{Path(meta.get('source_path','')).name}`")
        cols[2].caption(f"lines: `{meta.get('line_range','—')}`")
        with st.expander("Preview"):
            st.text(doc[:800])


def render_technical_result(meta: dict, doc: str, dist: float | None = None):
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**{meta.get('title', 'No title')}**")
            if bc := meta.get("breadcrumbs"):
                st.caption(bc)
        with c2:
            if dist is not None:
                score = round(1 - dist, 3)
                color = "#2ec4b6" if score > 0.7 else "#ff9f1c" if score > 0.4 else "#e71d36"
                st.markdown(
                    f"<span style='color:{color};font-weight:bold;font-size:1.1em'>▶ {score:.3f}</span>",
                    unsafe_allow_html=True,
                )
        xml_ref = meta.get("xml_reference", "")
        if xml_ref:
            st.code(xml_ref, language=None)
        cols = st.columns(2)
        cols[0].caption(f"source: `{Path(meta.get('source_path','')).name}`")
        cols[1].caption(f"markers: `{meta.get('line_range','—')}`")
        with st.expander("Shadow embedding text"):
            st.text(doc[:800])


def render_schema_result(meta: dict, doc: str, dist: float | None = None):
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(
                f"**`{meta.get('element_name','?')}`** "
                f"<span style='color:#888;font-size:0.85em'>({meta.get('attribute_count','?')} attrs)</span>",
                unsafe_allow_html=True,
            )
        with c2:
            if dist is not None:
                score = round(1 - dist, 3)
                color = "#2ec4b6" if score > 0.7 else "#ff9f1c" if score > 0.4 else "#e71d36"
                st.markdown(
                    f"<span style='color:{color};font-weight:bold;font-size:1.1em'>▶ {score:.3f}</span>",
                    unsafe_allow_html=True,
                )
        with st.expander("Full attribute spec", expanded=(dist is not None and (1 - dist) > 0.5)):
            st.text(doc)


RENDERERS = {
    COLLECTION_NAVIGATOR: render_navigator_result,
    COLLECTION_TECHNICAL: render_technical_result,
    COLLECTION_SCHEMA:    render_schema_result,
}


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🔍 GEOS DB Explorer")
    st.caption(f"Vector DB: `{VECTOR_DB_DIR}`")
    st.divider()

    st.subheader("Collections")
    col_counts = {name: collection_count(name) for name in COLLECTIONS}
    for name, info in COLLECTIONS.items():
        cnt = col_counts[name]
        status = "✅" if cnt > 0 else "❌"
        st.markdown(
            f"{status} {info['emoji']} **{info['label']}** "
            f"<span style='color:{info['color']}'>{cnt} chunks</span>",
            unsafe_allow_html=True,
        )

    st.divider()
    page = st.radio(
        "Page",
        ["🔎 Search", "📋 Browse", "📊 Stats"],
        label_visibility="collapsed",
    )


# ── Search page ───────────────────────────────────────────────────────────────

if page == "🔎 Search":
    st.header("🔎 Semantic Search")

    query = st.text_input(
        "Query",
        placeholder="e.g. 'ViscoDruckerPrager friction angle'  or  'hydraulic fracture solver'",
    )

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        selected = st.multiselect(
            "Search in",
            options=list(COLLECTIONS.keys()),
            default=list(COLLECTIONS.keys()),
            format_func=lambda n: f"{COLLECTIONS[n]['emoji']} {COLLECTIONS[n]['label']}",
        )
    with c2:
        n_results = st.slider("Results per collection", 1, 10, 3)
    with c3:
        st.write("")
        st.write("")
        search_btn = st.button("Search", type="primary", use_container_width=True)

    if not get_embedding_fn():
        st.warning("⚠️ No API key found — semantic search unavailable. Set OPENROUTER_API_KEY or OPENAI_API_KEY.")

    if search_btn and query and selected:
        for col_name in selected:
            info = COLLECTIONS[col_name]
            col = get_collection(col_name)
            if col is None:
                st.error(f"Collection `{col_name}` not found.")
                continue

            st.subheader(f"{info['emoji']} {info['label']}")
            with st.spinner(f"Querying {info['label']}..."):
                try:
                    results = col.query(
                        query_texts=[query],
                        n_results=n_results,
                        include=["documents", "metadatas", "distances"],
                    )
                    docs = results["documents"][0]
                    metas = results["metadatas"][0]
                    dists = results["distances"][0]

                    if not docs:
                        st.info("No results.")
                    else:
                        renderer = RENDERERS[col_name]
                        for doc, meta, dist in zip(docs, metas, dists):
                            renderer(meta, doc, dist)
                except Exception as e:
                    st.error(f"Search failed: {e}")
            st.divider()


# ── Browse page ───────────────────────────────────────────────────────────────

elif page == "📋 Browse":
    st.header("📋 Browse Collection")

    col_name = st.selectbox(
        "Collection",
        options=list(COLLECTIONS.keys()),
        format_func=lambda n: f"{COLLECTIONS[n]['emoji']} {COLLECTIONS[n]['label']} ({col_counts[n]} chunks)",
    )
    col = get_collection(col_name)

    if col is None:
        st.error(f"Collection `{col_name}` not found.")
    else:
        tab_browse, tab_filter, tab_raw = st.tabs(["🗂 Peek", "🔬 Filter by metadata", "📄 Raw JSON"])

        # ── Peek tab ──────────────────────────────────────────────────────────
        with tab_browse:
            peek_n = st.slider("Records to peek", 1, 50, 10, key="peek_n")
            if st.button("Peek", key="peek_btn"):
                result = col.peek(peek_n)
                renderer = RENDERERS[col_name]
                for doc, meta in zip(result["documents"], result["metadatas"]):
                    renderer(meta, doc)

        # ── Filter tab ────────────────────────────────────────────────────────
        with tab_filter:
            st.caption("Filter by metadata field value (exact string match).")

            # Dynamically determine filterable fields
            if col_name == COLLECTION_SCHEMA:
                filter_fields = ["element_name", "chunk_type", "attribute_count"]
            elif col_name == COLLECTION_NAVIGATOR:
                filter_fields = ["chunk_type", "breadcrumbs"]
            else:  # technical
                filter_fields = ["chunk_type", "breadcrumbs"]

            fc1, fc2, fc3 = st.columns([1, 2, 1])
            with fc1:
                field = st.selectbox("Field", filter_fields, key="filter_field")
            with fc2:
                value = st.text_input("Value", key="filter_value",
                                      placeholder="e.g. 'section' or 'ViscoDruckerPrager'")
            with fc3:
                limit = st.number_input("Limit", 1, 100, 20, key="filter_limit")

            if st.button("Filter", key="filter_btn") and value:
                try:
                    # attribute_count is stored as int
                    where_val: int | str = int(value) if field == "attribute_count" else value
                    results = col.get(
                        where={field: {"$eq": where_val}},
                        limit=int(limit),
                        include=["documents", "metadatas"],
                    )
                    docs = results["documents"]
                    metas = results["metadatas"]
                    st.caption(f"Found {len(docs)} records")
                    renderer = RENDERERS[col_name]
                    for doc, meta in zip(docs, metas):
                        renderer(meta, doc)
                except Exception as e:
                    st.error(f"Filter failed: {e}")

        # ── Raw JSON tab ──────────────────────────────────────────────────────
        with tab_raw:
            raw_n = st.slider("Records", 1, 20, 3, key="raw_n")
            if st.button("Load raw", key="raw_btn"):
                result = col.peek(raw_n)
                for i, (doc, meta, cid) in enumerate(
                    zip(result["documents"], result["metadatas"], result["ids"])
                ):
                    with st.expander(f"[{i}] `{cid}`"):
                        st.json({"id": cid, "metadata": meta, "document": doc})


# ── Stats page ────────────────────────────────────────────────────────────────

elif page == "📊 Stats":
    st.header("📊 Collection Statistics")

    for col_name, info in COLLECTIONS.items():
        col = get_collection(col_name)
        if col is None:
            st.warning(f"`{col_name}` not found.")
            continue

        with st.expander(
            f"{info['emoji']} **{info['label']}** (`{col_name}`) — {col_counts[col_name]} chunks",
            expanded=True,
        ):
            count = col_counts[col_name]
            st.metric("Total chunks", count)

            # Peek sample to derive schema
            sample = col.peek(min(count, 5))
            if sample["metadatas"]:
                st.subheader("Metadata fields")
                all_keys: set[str] = set()
                for m in sample["metadatas"]:
                    all_keys.update(m.keys())
                st.code(", ".join(sorted(all_keys)), language=None)

                st.subheader("Sample record")
                meta = sample["metadatas"][0]
                doc = sample["documents"][0]
                cid = sample["ids"][0]
                st.json({"id": cid, "metadata": meta})
                with st.expander("Document text"):
                    st.text(doc[:1000])

            # Schema-specific: list all element names
            if col_name == COLLECTION_SCHEMA:
                st.subheader("All indexed elements")
                all_results = col.get(include=["metadatas"])
                names = sorted(m["element_name"] for m in all_results["metadatas"])
                # Display as a compact multi-column list
                cols = st.columns(4)
                for i, name in enumerate(names):
                    cols[i % 4].code(name, language=None)

            # Navigator-specific: chunk type breakdown
            if col_name == COLLECTION_NAVIGATOR:
                st.subheader("Chunk type breakdown")
                all_results = col.get(include=["metadatas"])
                from collections import Counter
                counts = Counter(m.get("chunk_type", "?") for m in all_results["metadatas"])
                for ctype, cnt in counts.most_common():
                    st.markdown(f"- `{ctype}`: **{cnt}**")
