from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from state import AgentState
from tools import get_search_tool
import os

# Initialize LLM
llm = ChatGroq(temperature=0.5, model_name="llama-3.1-8b-instant", max_retries=5)
search_tool = get_search_tool()

# --- Pro Agent ---
def pro_agent(state: AgentState):
    """
    Argues FOR the topic.
    """
    topic = state["topic"]
    
    # Structured prompt for Pro agent
    system_msg = SystemMessage(content="""You are a skilled debater arguing IN FAVOR of the discussion topic. 
    Output logic:
    1. Be concise.
    2. Provide exactly 3 strong bullet points.
    3. Keep arguments under 50 words each.
    """)
    human_msg = HumanMessage(content=f"The topic is: {topic}. Present your best arguments.")
    
    # In a real tool-using agent, we might use bind_tools, but for simplicity we rely on the LLM's knowledge or simple invocation
    # If using tools, we'd bind them. For this "debate" structure, let's keep it direct.
    # To use tools using langgraph prebuilt agent or just simple chain:
    
    response = llm.invoke([system_msg, human_msg])
    
    return {"pro_argument": response.content, "messages": [response]}

import time

# --- Con Agent ---
def con_agent(state: AgentState):
    """
    Argues AGAINST the topic / Challenges the Pro argument.
    """
    print("\n[System]: Waiting to avoid rate limits...")
    time.sleep(20)
    
    topic = state["topic"]
    pro_arg = state["pro_argument"]
    
    system_msg = SystemMessage(content="""You are a skilled debater arguing AGAINST the discussion topic. 
    Output logic:
    1. Be concise.
    2. Directly refute the Pro arguments.
    3. Provide exactly 3 strong counter-point bullets.
    4. Keep arguments under 50 words each.
    """)
    human_msg = HumanMessage(content=f"The topic is: {topic}. The Pro side argued: {pro_arg}. Present your counter-arguments.")
    
    response = llm.invoke([system_msg, human_msg])
    
    return {"con_argument": response.content, "messages": [response]}

# --- Judge Agent ---
def judge_agent(state: AgentState):
    """
    Evaluates both sides and gives a verdict.
    """
    print("\n[System]: Waiting to avoid rate limits...")
    time.sleep(20)
    
    topic = state["topic"]
    pro_arg = state["pro_argument"]
    con_arg = state["con_argument"]
    
    system_msg = SystemMessage(content="""You are an impartial judge. 
    Output logic:
    1. Decide a winner.
    2. Provide a clear structure:
       **Winner:** [Pro/Con]
       **Reasoning:** [Brief explanation, max 2 sentences]
       **Key Takeaway:** [One distinct point]
    """)
    human_msg = HumanMessage(content=f"Topic: {topic}\n\nPro Argument: {pro_arg}\n\nCon Argument: {con_arg}\n\nWhat is your verdict?")
    
    response = llm.invoke([system_msg, human_msg])
    
    return {"verdict": response.content, "messages": [response]}
