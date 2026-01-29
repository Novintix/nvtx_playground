from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState
from src.retrieval import get_retriever
from src.tools import web_search_tool

# Initialize LLM
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.6)

def retrieve_node(state: AgentState):
    """
    Fetches context. 
    - If "Trainer Mode": Performs Web Search + Resume RAG.
    - If "Interview Mode": Prioritizes Resume Text for introductions, RAG for deep dives.
    """
    query = state["messages"][-1].content
    company = state["target_company"]
    mode = state["mode"]
    full_resume = state.get("resume_text", "")
    
    # 1. Internal RAG (Resume)
    # If the user just says "Start" or "Hello", RAG is useless. Use full resume summary.
    rag_context = ""
    retriever = get_retriever()
    
    if retriever and len(query) > 5: # Only RAG if query is substantial
        try:
            docs = retriever.invoke(query)
            rag_context = "\n".join([doc.page_content for doc in docs])
        except Exception:
            rag_context = ""
            
    # Fallback: If RAG is empty (or query is short), use the first 2000 chars of full resume
    if not rag_context and full_resume:
        rag_context = f"RESUME SUMMARY:\n{full_resume[:2000]}..."

    # 2. External Search (Only for Trainer Mode to save time/tokens)
    web_context = ""
    if "trainer" in mode.lower() and company:
        try:
            # Search specifically for questions
            search_query = f"{company} technical interview questions for freshers 2024 2025"
            web_context = web_search_tool.invoke(search_query)
        except Exception as e:
            web_context = f"Search currently unavailable: {e}"

    combined_context = f"""
    === RESUME CONTEXT ===
    {rag_context}
    
    === WEB SEARCH RESULTS (Latest Data) ===
    {web_context}
    """
    
    return {"retrieved_docs": combined_context}


def generate_node(state: AgentState):
    mode = state["mode"]
    context = state["retrieved_docs"]
    messages = state["messages"]
    company = state["target_company"]
    
    # Check conversation depth to control flow
    conversation_length = len(messages)
    
    if "trainer" in mode.lower():
        # --- TRAINER / MENTOR MODE ---
        system_prompt = f"""
        You are AURA, an Expert Interview Mentor.
        
        TASK:
        1. Analyze the [WEB SEARCH RESULTS] to find REAL interview questions asking by {company}.
        2. If specific questions are found, list 3 of them.
        3. For each, draft a "Winning Answer" using the user's [RESUME CONTEXT].
        
        FORMAT:
        - **Question:** ...
        - **Why it's asked:** ...
        - **Your Answer:** (Drafted in first person based on Resume)
        
        If the resume is missing info for a question, suggest what they should add.
        
        CONTEXT:
        {context}
        """
    else:
        # --- INTERVIEWER SIMULATION MODE ---
        # Logic: If it's the start (len <= 2), ask for intro. Don't critique "Start".
        
        if conversation_length <= 2:
            system_prompt = f"""
            You are a Senior Technical Recruiter at {company}. 
            You are starting an interview.
            
            YOUR GOAL: 
            Start the interview professionally. Do NOT critique anything yet.
            
            INSTRUCTION:
            1. Welcome the candidate.
            2. Ask them to "Introduce yourself" or "Walk me through your resume".
            3. Be brief and professional.
            """
        # Phase 2: The Grill (Subsequent Turns)
        else:
            system_prompt = f"""
            You are a Senior Technical Recruiter at {company}.
            You are conducting a live technical interview.
            
            CONTEXT:
            {context}
            
            STRICT RULES FOR RESPONSE:
            1. **ONE QUESTION ONLY**: You must ask EXACTLY ONE question. Never ask "Also, tell me about X...".
            2. **FOLLOW-UP LOGIC**: 
               - Look at the user's LAST answer. 
               - Pick ONE specific concept, tool, or project they mentioned.
               - Ask a "Why" or "How" question about that specific thing.
            3. **BE SKEPTICAL**: If they mention a complex tool (like RAG or LSTM), ask them to explain how it works internally.
            4. **SHORT & SHARP**: Keep your response under 3 sentences.
            
            BAD EXAMPLE (DO NOT DO THIS):
            "Great. Tell me about Django. Also how did you handle security? And what is RAG?"
            
            GOOD EXAMPLE:
            "That's interesting. You mentioned using LSTM for energy forecasting. Why did you choose LSTM over a simpler regression model for this specific dataset?"
            """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"messages": messages})
    
    return {"messages": [response]}