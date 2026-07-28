---
title: Crisis Response AI
emoji: 🚨
colorFrom: red
colorTo: gray
sdk: streamlit
sdk_version: 1.55.0
app_file: app.py
pinned: false
---

# Crisis Response AI — Multi-Agent Emergency Response

A multi-agent system that takes a raw, messy field report and produces a
commander-ready response: a structured situation assessment, a resource
allocation, a time-phased action plan, and the public and internal messaging
that goes with it.

Built with LangChain, Groq LLaMA 3.3 70B, Pydantic and Streamlit.

---

## Why it is built this way

The interesting problem in a multi-agent system is not getting an LLM to write a
plan — it is stopping one agent's sloppy output from silently poisoning every
agent downstream of it.

So the agents here do not pass each other prose. Every hand-off is a Pydantic
model with real constraints:

- severity must be 1–5, confidence 0.0–1.0, people at risk non-negative
- an assessment with no immediate threats or no hazards is rejected
- an action plan with no `0-1h` action is rejected — that is not a valid
  emergency plan
- the public alert is length-capped at 320 characters, because it has to fit an
  emergency broadcast

When validation fails, the model is handed its own output plus the exact
validation error and asked to correct itself, once. If it fails again the
pipeline raises rather than returning a confident-looking plan built on a
malformed assessment.

---

## Architecture

```
Raw field report
       │
       ▼
Situation Agent  ──► SituationAssessment   (severity, hazards, info gaps)
       │
       ▼
Resource Agent   ──► ResourcePlan          (allocations, shortfalls, escalation)
       │
       ▼
Planner Agent    ──► ActionPlan            (0-1h / 1-6h / 6-24h, owners, criteria)
       │
       ▼
Comms Agent      ──► CommunicationSet      (public alert, press, internal, do-not-say)
```

Each agent is a prompt plus a schema. `utils/structured.py` is the only place
that talks to the model, so validation and repair behaviour is identical
everywhere.

---

## Tech stack

| Tool | Purpose |
|---|---|
| LangChain Core | Message construction and model interface |
| Groq LLaMA 3.3 70B | Fast inference — the whole pipeline runs in seconds |
| Pydantic v2 | Inter-agent contracts and validation |
| Streamlit | Operator interface |

No vector store and no local model weights — the whole image is small enough to
cold-start on a free CPU Space in about a minute.

---

## Run locally

```bash
git clone https://github.com/PunyaVenkatesh/crisis-response-ai.git
cd crisis-response-ai
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`):

```
GROQ_API_KEY=your_groq_api_key_here
```

Run it:

```bash
streamlit run app.py
```

Three sample incidents are included — a bushfire, a flash flood and a chemical
release — so the app is demonstrable without writing a report first.

---

## Limitations

This is a decision-support prototype, not an operational emergency system. It
has no live data feeds, no access to real resource availability, and its
assessments are only as good as the report it is given. Any real deployment
would need human sign-off at every phase boundary.

---

## Author

Punya Venkatesh — Master of AI, Monash University
[GitHub](https://github.com/PunyaVenkatesh) · [LinkedIn](https://www.linkedin.com/in/punya-venkatesh)
