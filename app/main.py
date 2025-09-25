from __future__ import annotations
import os, sys, pathlib, re
from typing import List, Dict, Any
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# --- path bootstrap (top of app/main.py) ---
THIS_FILE = pathlib.Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parent.parent  # one level up from /app
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Prefer absolute import; fall back to relative if needed
try:
    from app.rag import RAGIndex
    from app.modes import MODES
    from app.voice import PERSONA
    from app.data_store import load_profile
except Exception:
    from .rag import RAGIndex
    from .modes import MODES
    from .voice import PERSONA
    from .data_store import load_profile

load_dotenv()  # loads EMERGENCY_PIN_HASH, PATIENT_JSON_PATH, etc.

# Use Streamlit secrets if env vars aren’t present
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
try:
    OPENAI_API_KEY = OPENAI_API_KEY or st.secrets.get("OPENAI_API_KEY")
except Exception:
    pass

st.set_page_config(page_title="Emergency Medical Profile Agent", page_icon="🚑", layout="wide")

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## Settings")

    # Prefer the emergency-focused modes if present
    modes_list = list(MODES.keys())
    default_index = modes_list.index("Emergency guidance") if "Emergency guidance" in modes_list else 0
    mode_name = st.selectbox("Mode", modes_list, index=default_index)

    rag_enabled = st.toggle(
        "Use RAG (retrieval)",
        value=os.environ.get("RAG_ENABLED", "true").lower() == "true",
    )
    top_k = st.slider("Top-k passages", 1, 10, int(os.environ.get("TOP_K", 5)))
    temperature = st.slider("Temperature", 0.0, 1.0, float(os.environ.get("TEMPERATURE", 0.5)))
    model_name = st.text_input("Model name", os.environ.get("MODEL_NAME", "gpt-4o-mini"))
    st.caption("Chat answers about the patient use RAG when enabled (for leaflets/notes).")

    # --- Emergency shortcuts ---
    st.markdown("## 🚑 Emergency")
    if st.button("Open Emergency Mode"):
        # Assumes file exists at app/pages/emergency.py
        st.switch_page("app/pages/emergency.py")

    # Optional: show a QR to open Emergency Mode (works for local dev)
    show_qr = st.checkbox("Show Emergency QR", value=False)
    if show_qr:
        try:
            from app.utils.qr_utils import make_qr
            emergency_url = os.environ.get(
                "EMERGENCY_URL",
                "http://localhost:8501/app/pages/emergency",  # Streamlit default dev server
            )
            st.image(make_qr(emergency_url))
            st.caption(emergency_url)
        except Exception as e:
            st.warning(f"QR unavailable: {e}")

# ---------- Header ----------
st.title("Emergency Medical Profile Agent")

# ---------- Patient summary card (always visible on home) ----------
try:
    prof = load_profile()
    colA, colB, colC = st.columns([2, 1, 1])
    with colA:
        st.subheader(prof["profile"].get("full_name", ""))
        st.caption(
            f"DOB: {prof['profile'].get('dob','')} · Blood: {prof['profile'].get('blood_type','')}"
        )
        aid = prof["profile"].get("medical_aid", {})
        st.write(f"**Medical aid**: {aid.get('provider','')} — {aid.get('plan','')}")
        if aid.get("emergency_hotline"):
            st.write(f"**Emergency hotline**: {aid.get('emergency_hotline')}")
    with colB:
        st.markdown("**Allergies**")
        for a in prof.get("allergies", [])[:3]:
            st.write(f"• {a.get('substance')} — {a.get('severity','')}")
    with colC:
        st.markdown("**Conditions**")
        for c in prof.get("conditions", [])[:3]:
            st.write(f"• {c.get('name')} ({c.get('severity','')})")
except Exception as e:
    st.info(f"Unable to load patient profile yet: {e}")

st.divider()

# ---------- Chat about the patient’s health profile ----------
st.markdown("### Ask a question about the patient’s medical history, meds, or device usage")

# Ensure index availability (lazy)
@st.cache_resource(show_spinner=False)
def load_index() -> RAGIndex:
    idx = RAGIndex()
    try:
        idx.load()
    except Exception as e:
        st.info("Index not found or failed to load. Upload docs to `data/raw/` and run `make reindex`.")
        raise e
    return idx

# Simple chat state
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of dicts: {role, content}

def llm_respond(system_prompt: str, user_prompt: str, temperature: float, model: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY") or (
        st.secrets.get("OPENAI_API_KEY") if hasattr(st, "secrets") else None
    )
    if not api_key:
        return "⚠️ OPENAI_API_KEY not set. Please configure your .env file."

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return resp.choices[0].message.content or ""

with st.container(border=True):
    q = st.chat_input('e.g., "How do I use the HandiHaler?" or "Where is the inhaler kept?"')
    if q:
        st.session_state.messages.append({"role": "user", "content": q})

# Render history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# On new user input, answer
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_q = st.session_state.messages[-1]["content"]
    mode = MODES[mode_name]

    retrieved: List[Dict[str, Any]] = []
    citations = ""

    if rag_enabled:
        try:
            idx = load_index()
            retrieved = idx.retrieve(last_q, k=top_k, rerank=False)
            if retrieved:
                preview = []
                import os as _os
                for r in retrieved:
                    head = f"{r['cite_id']} {_os.path.basename(r.get('source_name') or r['source'])} · chunk {r['chunk_id']}"
                    body = r["text"].replace("\n", " ").strip()
                    if len(body) > 300:
                        body = body[:300] + "…"
                    preview.append(f"**{head}**\n\n> {body}")
                citations = "\n\n---\n\n".join(preview)
        except Exception as e:
            st.warning(f"Retrieval failed: {e}")

    # System prompt focused on emergency usability and accuracy
    sys_prompt = (
        f"{mode.system}\n\n"
        f"{PERSONA}\n\n"
        "You are a medical profile assistant for emergencies. "
        "Only use facts from the patient's structured profile and retrieved documents (e.g., device leaflets). "
        "Prioritise safety: list concise steps (≤12 words each), surface storage locations, allergies, and dosage clearly. "
        "If confidence is low or instructions are incomplete, say so and advise seeking professional help. "
        "Do not invent facts."
    )

    user_prompt = last_q

    if rag_enabled and retrieved:
        ctx = "\n\n".join(f"{r['cite_id']} {r['text']}" for r in retrieved)
        user_prompt = (
            f"Question: {last_q}\n\n"
            f"Use the following context if relevant. Cite using the bracketed ids [#].\n\n{ctx}\n\n"
            f"Style hint: {mode.style_hint}"
        )
    else:
        user_prompt = (
            f"Question: {last_q}\n\n"
            f"No reliable sources were retrieved. Answer briefly and cautiously, "
            f"call out uncertainty, and advise next safe actions. "
            f"Style hint: {mode.style_hint}."
        )

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            answer = llm_respond(
                sys_prompt, user_prompt, temperature=temperature, model=model_name
            )

            if answer.strip():
                st.markdown(answer)
                if citations:
                    with st.expander("Retrieved context & citations"):
                        st.markdown(citations)
            else:
                st.markdown("(No response)")

            st.session_state.messages.append({"role": "assistant", "content": answer})
