# Closira Core Intelligence Layer — LangGraph Agent Onboarding Flow

An enterprise-ready, multi-turn AI customer assistant built using **LangGraph, LangChain, and ChatGroq**. The assistant handles inbound customer queries, lead qualification, escalation detection, and automated session summarization using a structured SOP-driven workflow.

---

## Architecture Overview

The workflow consists of four stages:

### Stage 1 — FAQ Answering (`faq_node`)
- Answers customer queries strictly using the business SOP
- Prevents hallucination using explicit SOP grounding
- Detects out-of-scope questions

### Stage 2 — Lead Qualification (`lead_qualification_node`)
Collects structured lead information:
- Business Type / Industry
- Team Size
- Current Booking Tools

### Stage 3 — Escalation Handling (`escalation_node`)
Triggers human handoff when:
- user explicitly requests human support
- out-of-scope query is detected
- frustrated/angry interaction occurs

### Stage 4 — Session Summary (`summary_node`)
Generates a structured markdown report containing:
- Customer intent
- Lead qualification details
- SOP gaps
- Recommended next action

## 🛠️ System Dependencies & Requirements

To run this workflow pipeline locally, the following core dependencies must be installed:

* `langgraph` (v0.0+) — Handles structural state-graph node management and multi-turn routing configurations.
* `langchain-core` — Manages message object formatting (`HumanMessage`, `AIMessage`, `SystemMessage`).
* `langchain-groq` — Facilitates real-time API client connectivity to Groq cloud inference endpoints.
* `python-dotenv` — Safely parses environmental configuration parameters away from public commit histories.

