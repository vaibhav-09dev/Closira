# Prompt Engineering & System Design Documentation


## 1. System Prompt Architecture

### A. Stage 1: FAQ Node (`faq_node`)
* **Role**: Inbound Customer Assistant & Intake Router.
* **Objective**: Answer service and product inquiries accurately while identifying potential onboarding leads.
* **Design Framework**: Uses a strict boundary container system prompt embedding the raw Business SOP data directly into the LLM context. It explicitly prevents out-of-bounds knowledge retrieval.

### B. Stage 2: Qualification Node (`lead_qualification_node`)
* **Role**: Demographics Qualification Specialist.
* **Objective**: Collect missing profile vectors (`business_type`, `team_size`, `booking_tools`) sequentially without overwhelming the user.
* **Design Framework**: Employs a deterministic State Machine tracking logic alongside conversational transitions. This forces a single information-gathering block execution per conversation turn.

---

## 2. Hallucination Prevention Approach

To guarantee production-grade data reliability and compliance with enterprise operational parameters, the workflow implements a multi-tier defense layer against model hallucinations:

1.  **Context Lock Anchor**: The system prompt strictly limits response parameters to facts present in the provided business SOP dataset.
2.  **Structural Execution Guard**: Instead of counting on the LLM to cleanly update internal state variables via raw parsing—which risks loop dropouts and slot confusion—the app utilizes a deterministic condition chain (`if-elif-else`) in Python. This structure parses explicit user messages and accurately logs variables to the graph state.
3.  **Token Processing Isolation**: To prevent reasoning tokens (`<think>...</think>`) from bleeding into validation layers and falsely triggering exceptions, the graph strips reasoning tokens out before evaluating conditional routing logic.

---

## 3. Escalation and Exception Logic (Stage 3)

The architecture features an intercept hook to handle operational edge cases, out-of-scope inquiries, or direct human handoff requests:

* **Trigger Pattern Detection**: The system continuously monitors inputs and outputs for specific validation strings (`[TRIGGER_HUMAN_HANDOFF]`) or semantic matches (`human`, `operator`).
* **Handoff Interception Node (`escalation_node`)**: When a trigger condition is met, the workflow flags state variables (`is_escalated: True`), saves metadata regarding the breach event (`escalation_reason`), and safely exits the interactive runtime conversation loop to hand operations over to manual operators.