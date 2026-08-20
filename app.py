import os
from typing import TypedDict, Annotated

import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

load_dotenv()

st.set_page_config(page_title="SafeScript AI", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
.title {font-size:2.6rem;font-weight:800;margin-bottom:0}
.subtitle {color:#6b7280;font-size:1.05rem;margin-bottom:1.5rem}
.card {padding:1rem;border:1px solid rgba(128,128,128,.25);border-radius:14px;min-height:135px}
.value {font-size:2.2rem;font-weight:800}
.low {color:#16a34a}.medium {color:#d97706}.high {color:#dc2626}
</style>
""", unsafe_allow_html=True)


class AnalyzerState(TypedDict):
    raw_text: str
    safety_scores: Annotated[dict[str, int], lambda old, new: {**(old or {}), **(new or {})}]


@st.cache_resource
def build_graph():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None

    llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.7, api_key=key)

    def score(prompt):
        try:
            return max(0, min(100, int(llm.invoke(prompt).content.strip())))
        except (ValueError, TypeError):
            return 0

    def toxicity(state):
        return {"safety_scores": {"toxicity_level": score(
            "Analyze this text for profanity, aggression, hate speech, or toxicity. "
            "Return ONLY an integer from 0 to 100. 0=clean, 100=highly toxic.\n\n"
            + state["raw_text"]
        )}}

    def copyright(state):
        return {"safety_scores": {"copyright_risk": score(
            "Analyze this text for plagiarism-like language, unoriginality, or "
            "corporate trademark risk. Return ONLY an integer from 0 to 100. "
            "0=original, 100=high risk.\n\n" + state["raw_text"]
        )}}

    def culture(state):
        return {"safety_scores": {"cultural_insensitivity": score(
            "Analyze this text for regional sensitivity, political landmines, or "
            "cultural insensitivity. Return ONLY an integer from 0 to 100. "
            "0=safe, 100=highly offensive.\n\n" + state["raw_text"]
        )}}

    g = StateGraph(AnalyzerState)
    g.add_node("toxicity_node", toxicity)
    g.add_node("copyright_check", copyright)
    g.add_node("culture_node", culture)
    g.add_edge(START, "toxicity_node")
    g.add_edge(START, "copyright_check")
    g.add_edge(START, "culture_node")
    g.add_edge("toxicity_node", END)
    g.add_edge("copyright_check", END)
    g.add_edge("culture_node", END)
    return g.compile()


def risk(score):
    if score < 34: return "Low", "low"
    if score < 67: return "Medium", "medium"
    return "High", "high"


def card(title, icon, score):
    label, css = risk(score)
    st.markdown(
        f'<div class="card"><div>{icon} <b>{title}</b></div>'
        f'<div class="value {css}">{score}<small>/100</small></div>'
        f'<div class="{css}"><b>{label} risk</b></div></div>',
        unsafe_allow_html=True,
    )


st.markdown('<div class="title">🛡️ SafeScript AI</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Parallel AI content safety analysis using LangGraph reducers.</div>',
    unsafe_allow_html=True
)

with st.sidebar:
    st.header("⚙️ About")
    st.write("SafeScript sends the same input to three independent analysis branches.")
    st.markdown("**Branches**")
    st.write("☣️ Toxicity")
    st.write("🔐 Copyright")
    st.write("🌍 Cultural sensitivity")
    st.markdown("**Flow**")
    st.code("START\n ├─ Toxicity\n ├─ Copyright\n └─ Culture\n       ↓\n    Reducer\n       ↓\n    Report")

st.subheader("Analyze your content")

example = (
    "Yo guys! Welcome back to the stream. Today I am going to show you how to "
    "hack into your friend's system using a script I copied directly from an "
    "online forum. Traditional security protocols are absolute garbage and "
    "anyone still using them is an idiot."
)

text = st.text_area(
    "Content",
    height=220,
    placeholder="Paste a script, article, post, or other text here...",
    label_visibility="collapsed",
)

a, b, c = st.columns(3)
with a:
    analyze = st.button("🔍 Analyze Content", type="primary", use_container_width=True)
with b:
    if st.button("📝 Load Example", use_container_width=True):
        st.session_state["example"] = example
        st.rerun()
with c:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.pop("results", None)
        st.session_state.pop("example", None)
        st.rerun()

if "example" in st.session_state and not text:
    text = st.session_state["example"]

if analyze:
    if not text.strip():
        st.warning("Please enter some text first.")
    elif not os.getenv("GROQ_API_KEY"):
        st.error("GROQ_API_KEY is missing. Create a .env file with your Groq API key.")
    else:
        graph = build_graph()
        with st.spinner("Running three parallel LangGraph safety checks..."):
            try:
                result = graph.invoke({"raw_text": text.strip(), "safety_scores": {}})
                st.session_state["results"] = result["safety_scores"]
            except Exception as e:
                st.error("Analysis failed.")
                st.exception(e)

results = st.session_state.get("results")

if results:
    st.divider()
    st.subheader("Safety Report")

    t = int(results.get("toxicity_level", 0))
    c = int(results.get("copyright_risk", 0))
    cu = int(results.get("cultural_insensitivity", 0))
    overall = round((t + c + cu) / 3)
    overall_label, _ = risk(overall)

    x, y, z = st.columns(3)
    with x: card("Toxicity", "☣️", t)
    with y: card("Copyright Risk", "🔐", c)
    with z: card("Cultural Sensitivity", "🌍", cu)

    st.markdown("### Overall Risk")
    st.progress(overall / 100)
    st.write(f"**{overall_label} — {overall}/100**")

    st.markdown("### LangGraph Architecture")
    p1, p2, p3, p4 = st.columns(4)
    p1.info("📄 Input")
    p2.info("☣️ 🔐 🌍\nParallel branches")
    p3.info("🔄 Reducer\nMerge scores")
    p4.success("📊 Report")

    with st.expander("View raw LangGraph result"):
        st.json(results)

    report = (
        "SafeScript AI Report\n\n"
        f"Toxicity: {t}/100\n"
        f"Copyright Risk: {c}/100\n"
        f"Cultural Sensitivity: {cu}/100\n"
        f"Overall Risk: {overall}/100 ({overall_label})\n"
    )
    st.download_button(
        "⬇️ Download Report",
        report,
        "safescript-report.txt",
        "text/plain",
    )

st.caption("AI-generated risk estimates; not legal advice or a definitive moderation decision.")
