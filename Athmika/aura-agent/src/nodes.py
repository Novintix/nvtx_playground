from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
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
    
    if retriever and len(query) > 10: # Only RAG if query is substantial
        try:
            docs = retriever.invoke(query)
            rag_context = "\n".join([doc.page_content for doc in docs])
        except:
            pass
            
    # Fallback: If RAG is empty (or query is short), use the first 2000 chars of full resume
    if not rag_context and full_resume:
        rag_context = f"RESUME SUMMARY:\n{full_resume[:2000]}..."
    # 2. External Search (Only for Trainer Mode to save time/tokens)
    web_context = ""
    if "trainer" in mode.lower() and company:
        try:
            # Search specifically for questions
            search_query = f"{company} technical interview questions for freshers 2025 2026"
            raw_search = web_search_tool.invoke(search_query)
            if isinstance(raw_search, str):
                web_context = "TOP SEARCH RESULTS:\n"
                for i, res in enumerate(raw_search):
                    web_context += f"SOURCE{i+1}.\nURL: {res.get('url')}\nCONTENT: {res.get('content')}\n\n"
            else:
                web_context = str(raw_search)
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
    current_depth = state.get("topic_depth", 0)
    new_depth = current_depth
    
    # Check conversation depth to control flow
    conversation_length = len(messages)
    
    if "trainer" in mode.lower():
        # --- TRAINER / MENTOR MODE ---
        system_prompt = f"""
        You are AURA, an Expert Technical Interview Mentor for students.
        
        INPUT DATA:
        1. **RESUME CONTEXT**: The candidate's actual projects and skills.
        2. **REAL INTERVIEW SOURCES**: A list of search results with "URL" and "CONTENT" containing real questions asked at {company}.
        
        TASK:
        1. **Topic Identification**: Look at the user's last message. 
           - If they asked for specific topics (e.g., "Python questions"), filter for those.
           - If they just said "Start" or "Help", pick the top 3 most frequent technical questions found in the search results.
           
        2. **Question Selection**: Select 3 distinct REAL interview questions from the [REAL INTERVIEW SOURCES].
            Scan the [SOURCES] for questions asked at {company}.
            **FILTERING RULE (CRITICAL):** - **IGNORE** simple fact-based questions like "Define Polymorphism."
           - **SELECT ONLY** behavioral or project-based questions (e.g., "Describe a challenge...", "Tell me about a time you used...", "Explain the architecture of...").
        
        3. **Drafting the Solution**: For *each* question:
           - **Extract Source**: Copy the exact `URL` where you found this question.
           - **Draft Answer**: Write a "Winning Answer" in the first person ("I...") using the [RESUME CONTEXT]. 
           - **Explain Logic**: Briefly explain *why* this answer is strong (e.g., "It mentions your specific project X...").
        
        STRICT RULES:
        - If the resume does not have enough info to answer a specific question, admit it in the "Ideal Answer" section and suggest what project/skill they should add.
        - Do NOT invent URLs. Use the ones provided in the search results.
        
        OUTPUT FORMAT:
       ### 🎯 Question [1/2/3]
        **❓ Real Question:** [Insert Question Text from Search]
        **🔗 Source:** [Insert Exact URL from Search Result]

        **✅ Ideal Answer:** [First-person answer drafting using resume data and RESUME data alone. Don't try to build on knowledge outside the resume.]

        **💡 The Logic:** [Why this answer is good?]
        
        
        CONTEXT:
        {context}
        """
        new_depth = 0

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
            new_depth = 0
        # Phase 2: The Grill (Subsequent Turns)
        else:
            if current_depth >= 2:
                instruction = "TRANSITION: The candidate has answerd enough on this move. Ensure a smooth transistion to a DIFFERENT topic about their skills in their resume."
                new_depth = 0
            else:
                instruction = "DRILL DEEP: The candidate just answered. Pick ONE specific technical detail they mentioned and ask a 'Why' or 'How' follow-up question."
                new_depth = current_depth + 1
            system_prompt = f"""
            You are a Senior Technical Recruiter at {company}.
            You are conducting a live technical interview.
            
            CONTEXT:
            {context}
            
            TASK:
            1. **SCORE CARD**: Evaluate the user's answer (0-10).
               - Technical Accuracy: Did they use correct terminology?
               - Clarity: Was it structured (STAR format)?
            2. **GAP ANALYSIS**: Briefly mention one thing they missed or could improve.
            3. **NEXT QUESTION**: {instruction}
            
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
            
            OUTPUT FORMAT:
            📊 **Score Card**
            * **Technical:** X/10
            * **Clarity:** Y/10
            
            📉 **Feedback**
            [1 sentence critique]
            
            🎤 **Next Question**
            [Your Question Here]
            """


    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content = system_prompt),
        ("placeholder", "{messages}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"messages": messages})
    
    return {"messages": [response],
            "topic_depth": new_depth}