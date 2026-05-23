import os
import json
from typing import Annotated, Literal, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

load_dotenv()


try:
    with open("sop.txt", "r") as f:
        SOP_DATA = f.read()
except FileNotFoundError:
    
    SOP_DATA = """
    COMPANY NAME: Closira Partner Clinic (Radiance MedSpa)
    SERVICES AND PRICING:
    - Botox Injections: $12 per unit. Used for forehead lines and crow's feet.
    - Juvederm Dermal Fillers: $650 per syringe. Used for lip plumbing and volume loss.
    - Laser Facial Toning: $200 per session. Treats hyperpigmentation.
    
    LEAD QUALIFICATION SCRIPT:
    If a customer wants to book or shows high interest, you must collect:
    1. Business Type / Industry (e.g., local salon, retail, corporate)
    2. Team Size
    3. Current booking tools utilized
    """


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    lead_details: dict         
    is_escalated: bool         
    escalation_reason: str     
    summary: str               


llm = ChatGroq(model="qwen/qwen3-32b")


def faq_node(state: AgentState):
    """Stage 1 & 3: Answers questions STRICTLY using the SOP data file.
    Also evaluates if the user request warrants an immediate escalation."""
    messages = state["messages"]
    user_input = messages[-1].content

    system_prompt = f"""You are Closira's AI Customer Assistant running an onboarding flow. 
    Your primary goal is answering inbound customer inquiries using ONLY the verified business SOP below.

    BUSINESS SOP RULES:
    {SOP_DATA}

    CRITICAL RULES: 
    1. Respond ONLY from the facts present in the SOP. Do NOT make up information or hallucinate prices.
    2. If a user explicitly states they want to book an appointment or expresses high interest in a service (like Botox or Fillers), this is completely IN-SCOPE. Do NOT trigger a human handoff for booking requests. Simply confirm the service details politely.
    3. If the user's question cannot be answered by the SOP data at all (e.g., asking about services not listed, pricing not in the file), or if they ask for a human agent, you must prepend your response with the phrase: [TRIGGER_HUMAN_HANDOFF]
    
    Current Conversation History:
    """ 
    formatted_messages = [SystemMessage(content=system_prompt)] + messages
    response = llm.invoke(formatted_messages)
    content = response.content

    # Stage 3 Interception Logic
    if "[TRIGGER_HUMAN_HANDOFF]" in content or "human" in user_input.lower() or "operator" in user_input.lower():
        clean_content = content.replace("[TRIGGER_HUMAN_HANDOFF]", "").strip()
        if not clean_content:
            clean_content = "I'm going to connect you with a team member who can help resolve this for you immediately."
        return {
            "messages": [AIMessage(content=clean_content)],
            "is_escalated": True,
            "escalation_reason": f"Out-of-scope or explicit operator request detected on input: '{user_input}'"
        }

    return {"messages": [response]}


def lead_qualification_node(state: AgentState):
    """Stage 2: Gathers structured lead demographics (Business type, team size, tools)."""
    messages = state["messages"]
    
    system_prompt = """You are an AI assistant qualifying an incoming business lead.
    Review the current chat history. Your goal is to collect the remaining missing details from this list:
    - Business Type
    - Team Size
    - Current Software Tools
    
    Acknowledge their previous response nicely, and ask for ONE missing detail at a time in a friendly, conversational manner.
    """
    formatted_messages = [SystemMessage(content=system_prompt)] + messages
    response = llm.invoke(formatted_messages)
    
    
    return {"messages": [response]}


def escalation_node(state: AgentState):
    """Stage 3 Execution: Flags handoff and logs tracking telemetry data."""
    print(f"\n>>> [SYSTEM METRIC LOG]: Escalation triggered successfully.")
    print(f">>> [REASON]: {state.get('escalation_reason')}\n")
    return {"is_escalated": True}


def summary_node(state: AgentState):
    """Stage 4: Compiles final structured session metadata at termination."""
    messages = state["messages"]
    
    summary_prompt = f"""Analyze the entire conversation thread and output a clear, structured Markdown report covering:
    1. Customer Intent
    2. Key Details / Demographics Collected
    3. SOP Gaps Identified (What did they ask that wasn't covered in the SOP data file?)
    4. Recommended Next Action for Closira staff

    Conversation History:
    {[m.content for m in messages]}
    """
    
    response = llm.invoke([SystemMessage(content=summary_prompt)])
    return {"summary": response.content}


def route_after_faq(state: AgentState) -> Literal["escalation", "qualification", "summary"]:
    """Conditional router parsing state parameters."""
    if state.get("is_escalated"):
        return "escalation"
    
    
    last_user_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content.lower()
            break
            
    if "book" in last_user_msg or "appointment" in last_user_msg or "yes" in last_user_msg or "sure" in last_user_msg:
        return "qualification"
        
    return "summary"


workflow = StateGraph(AgentState)

workflow.add_node("faq", faq_node)
workflow.add_node("qualification", lead_qualification_node)
workflow.add_node("escalation", escalation_node)
workflow.add_node("summary", summary_node)

workflow.set_entry_point("faq")

workflow.add_conditional_edges("faq", route_after_faq)
workflow.add_edge("qualification", "summary")
workflow.add_edge("escalation", "summary")
workflow.add_edge("summary", END)


app = workflow.compile()


if __name__ == "__main__":
    print("==================================================")
    print(" CLOSIRA CORE INTELLIGENCE LAYER — ACTIVE          ")
    print("==================================================")
    print("Type 'exit' to gracefully end the loop.\n")
    
    
    current_state = {
        "messages": [],
        "lead_details": {},
        "is_escalated": False,
        "escalation_reason": "",
        "summary": ""
    }
    
    while True:
        user_text = input("User: ")
        if user_text.strip().lower() == 'exit':
            
            final_output = app.invoke({"messages": current_state["messages"]})
            print("\n" + "="*40 + "\nFINAL MEETING SUMMARY REPT:\n" + "="*40)
            print(final_output.get("summary"))
            break
            
        
        current_state["messages"].append(HumanMessage(content=user_text))
        
        
        output_state = app.invoke(current_state)
        
        
        latest_reply = output_state["messages"][-1].content
        print(f"AI (Closira): {latest_reply}\n")
        
        
        current_state = output_state
        
        
        if output_state.get("is_escalated"):
            print("--- CHAT TERMINATED BY LIVE ESCALATION HOOK ---")
            print("\n" + "="*40 + "\nSTAGE 4: AUTOMATED CLOSIRA SUMMARY REPORT:\n" + "="*40)
            print(output_state.get("summary"))
            break