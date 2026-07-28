"""Crisis Response AI — Streamlit front end."""

import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from core.pipeline import AGENT_ORDER, DEFAULT_INVENTORY, run_pipeline

load_dotenv()

st.set_page_config(page_title="Crisis Response AI", page_icon="🚨", layout="wide")

SAMPLES = json.loads(
    (Path(__file__).parent / "data" / "sample_incidents.json").read_text(
        encoding="utf-8"
    )
)

SEVERITY_LABELS = {
    1: "Minor — local response",
    2: "Moderate — district response",
    3: "Serious — regional response",
    4: "Major — state response",
    5: "Catastrophic — national response",
}


def severity_colour(sev: int) -> str:
    return {1: "green", 2: "green", 3: "orange", 4: "red", 5: "red"}.get(sev, "grey")


# --------------------------------------------------------------------------- UI
st.title("🚨 Crisis Response AI")
st.markdown(
    "#### A multi-agent system that turns a raw field report into an actionable "
    "emergency response"
)
st.markdown("---")

with st.sidebar:
    st.header("Incident input")

    choice = st.selectbox(
        "Start from a sample incident", ["— write my own —"] + list(SAMPLES)
    )
    default_report = "" if choice == "— write my own —" else SAMPLES[choice]

    report = st.text_area(
        "Field report",
        value=default_report,
        height=240,
        placeholder="Paste the raw incident report as it came in from the field...",
    )

    with st.expander("Available resources"):
        inventory = st.text_area(
            "Inventory", value=DEFAULT_INVENTORY, height=170, label_visibility="collapsed"
        )

    run_btn = st.button("Run response pipeline", use_container_width=True, type="primary")

    st.caption(
        "Four agents run in sequence: Situation → Resources → Plan → Communications. "
        "Each hands the next a schema-validated object."
    )

    if not os.getenv("GROQ_API_KEY"):
        st.error("GROQ_API_KEY is not set. Add it as a Secret before running.")

if run_btn and report.strip():
    progress = st.progress(0.0, text="Starting...")

    def on_step(i: int, label: str):
        progress.progress(i / len(AGENT_ORDER), text=f"{AGENT_ORDER[i][0]}: {label}")

    try:
        result = run_pipeline(report, inventory=inventory, on_step=on_step)
        progress.progress(1.0, text="Response ready")
        st.session_state.result = result
    except Exception as err:  # noqa: BLE001 — surface the real failure to the operator
        progress.empty()
        st.error(f"Pipeline failed: {err}")

result = st.session_state.get("result")

if result:
    a, r, p, c = result.assessment, result.resources, result.plan, result.comms

    top = st.columns(4)
    top[0].metric("Severity", f"{a.severity}/5", SEVERITY_LABELS[a.severity])
    top[1].metric("People at risk", f"{a.people_at_risk:,}")
    top[2].metric("Assessment confidence", f"{a.confidence:.0%}")
    top[3].metric(
        "Escalation", "REQUIRED" if r.escalation_required else "Not required"
    )

    st.markdown(
        f":{severity_colour(a.severity)}[**{a.incident_type}** — {a.location}]"
    )

    tabs = st.tabs(
        ["Situation", "Resources", "Action plan", "Communications", "Raw output"]
    )

    with tabs[0]:
        st.subheader("Immediate threats")
        for t in a.immediate_threats:
            st.markdown(f"- {t}")

        st.subheader("Hazards")
        st.dataframe(
            [
                {"Hazard": h.name, "Likelihood": h.likelihood, "Impact": h.impact}
                for h in a.hazards
            ],
            use_container_width=True,
            hide_index=True,
        )

        if a.information_gaps:
            st.subheader("Information gaps")
            st.info("\n".join(f"- {g}" for g in a.information_gaps))

    with tabs[1]:
        st.subheader("Allocations")
        st.dataframe(
            [
                {
                    "Resource": x.resource,
                    "Qty": x.quantity,
                    "Assigned to": x.assigned_to,
                    "Rationale": x.rationale,
                }
                for x in r.allocations
            ],
            use_container_width=True,
            hide_index=True,
        )
        if r.shortfalls:
            st.subheader("Shortfalls")
            for s in r.shortfalls:
                st.warning(s)

    with tabs[2]:
        st.subheader(p.objective)
        for phase in ("0-1h", "1-6h", "6-24h"):
            actions = sorted(
                [x for x in p.actions if x.phase == phase], key=lambda x: x.priority
            )
            if not actions:
                continue
            st.markdown(f"##### {phase}")
            for x in actions:
                with st.expander(f"P{x.priority} · {x.owner} — {x.task}"):
                    st.markdown(f"**Success criteria:** {x.success_criteria}")
        if p.key_risks:
            st.subheader("Key risks")
            for k in p.key_risks:
                st.markdown(f"- {k}")

    with tabs[3]:
        st.subheader("Public alert")
        st.success(c.public_alert)
        st.caption(f"{len(c.public_alert)} characters")

        st.subheader("Press statement")
        st.write(c.press_statement)

        st.subheader("Internal brief")
        st.write(c.internal_brief)

        if c.do_not_say:
            st.subheader("Do not say")
            for d in c.do_not_say:
                st.error(d)

    with tabs[4]:
        st.json(result.model_dump())

    st.download_button(
        "Download incident brief (JSON)",
        data=result.model_dump_json(indent=2),
        file_name="incident_response.json",
        mime="application/json",
    )

elif not run_btn:
    cols = st.columns(4)
    for col, (name, what) in zip(cols, AGENT_ORDER):
        col.info(f"**{name}**\n\n{what}")
    st.caption(
        "Pick a sample incident in the sidebar, or paste your own field report, "
        "then run the pipeline."
    )
