from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from src.state import AgentState
from src.retrieval import get_retriever
from src.tools import web_search_tool

# Initialize LLM
llm = ChatGroq(model = "llama-3.3-70b-versatile", temperature=0.6)

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
            if len(query) < 50: # If it's a short topic like "Java" or "Python"
                search_query = f"{company} {query} technical interview questions for freshers 2025 2026"
            else:
                # If it's a long sentence, fall back to generic or extract keywords (simple fallback here)
                search_query = f"{company} technical interview questions for freshers"
            
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
    last_user_msg = messages[-1].content
    current_depth = state.get("topic_depth", 0)
    new_depth = current_depth
    
    # Check conversation depth to control flow
    conversation_length = len(messages)
    
    if "trainer" in mode.lower():
        # --- 1. INTENT ROUTER (The Switch) ---
        # We classify if the user wants internal help (Resume) or external info (Market).
        system_prompt = f"""
        Classify the user's intent into exactly one of these two categories:
        
        1. "RESUME_HELP": The user wants help explaining, summarizing, or pitching THEIR OWN specific projects/skills (e.g. "Explain WellGenix", "Help me with my intro", "How do I talk about Python?").
            - Triggers: "Explain my project", "My Python skills", "How do I pitch WellGenix?", "Tell me about me".
        2. "MARKET_INFO": The user wants to know about external interview questions, company trends, or generic question banks (e.g. "Start", "What does CTS ask?", "Common questions").
            - Triggers: "Java", "Python", "SQL", "CTS Questions", "What does Cognizant ask?", "System Design".
        3. "OFF_TOPIC": User asks about general knowledge, celebrities, movies, sports, politics or chit-chat (e.g. "Who is Billie Eilish?", "What is the weather?")
        
        USER MESSAGE: "{messages[-1].content}"
        
        Reply ONLY with the category name.
        """
        # Call LLM to decide
        intent = llm.invoke(system_prompt).content.strip().upper()
        
        # --- 2. BRANCHING BASED ON INTENT ---

        if "RESUME_HELP" in intent:
            # === PATH A: RESUME COACH (Internal Only, NO URLs) ===
            system_prompt = f"""
            You are AURA, a strict Resume Strategy Coach.
            
            INPUT DATA:
            1. **RESUME**: Candidate's actual projects.
            2. **TOPIC**: User wants to explain "{last_user_msg}". if the project is not in the resume, say "NOT_FOUND".
            
            TASK:
            1. **VERIFY**: Search the [RESUME CONTEXT] for the specific project/skill mentioned in the USER QUERY.
            2. **DECIDE**:
               - **IF FOUND**: Draft a pitch script using ONLY the resume details.
                    **Simulate a Question:** Generate a realistic technical or behavioral question an interviewer would ask about this specific project/skill.
                    **Draft the Answer:** Write a "Winning Answer" using ONLY facts from the resume.
                    **Analyze:** Explain the logic.
               - **IF NOT FOUND**: You MUST refuse to answer. Do not use general knowledge.
            
            STRICT RULES:
            - **NO URLs:** Do NOT include a "Source" or "Link".
            - **NO HALLUCINATION:** Use strictly the tools/tech listed in the resume.
            🚨 TECH STACK PRECISION RULES:
            - **EXACT TERMINOLOGY:** Do NOT generalize tools.
              - If resume says "FlutterFlow", say "FlutterFlow". Do NOT say "Flutter".
              - If resume says "Java", do NOT say "SpringBoot" unless explicitly listed.
            - **NO HALLUCINATION:** Only mention features actually listed in the context.
            
            OUTPUT FORMAT (STRICTLY ONLY IF PROJECT FOUND):
            
            ### 🎯 Explaining "{last_user_msg}"
            
            **❓ Anticipated Question:** [Generate a likely question, e.g., "Can you walk me through..."]
            
            **✅ Ideal Answer:** [Draft the perfect First-Person response]
            
            **💡 The Logic:** [1 sentence summary]
            
            **🚀 Why this is strong:**
            1. **Technical Depth:** [Mention specific tools used]
            2. **Role:** [Highlight individual contribution]
            3. **Impact:** [Mention results/problem solved]
            
             OUTPUT FORMAT (IF PROJECT NOT FOUND):
            ### ⚠️ Project Missing
            **Analysis:** I scanned your resume but could not find any mention of the project "[Insert Extracted Project Name Here]". 
            
            **Advice:** As a strict resume coach, I only help you pitch projects you have actually listed. Please upload a new resume containing this project.

            CONTEXT:
            {context}
            """
            new_depth = 0
            
        elif "MARKET_INFO" in intent:
            # === PATH B: MARKET SCOUT (Strict "Real Question" Filter) ===
            system_prompt = f"""
            You are AURA, an Expert Technical Interview Mentor.
            
            INPUT DATA:
            1. **RESUME CONTEXT**: The candidate's actual projects and skills.
            2. **REAL INTERVIEW SOURCES**: Search results for {company} interviews.
            
            TASK:
            Identify what the user is asking about:
            1. If they ask about questions related to {company} Find 3 specific interview questions that are **EXPLICITLY QUOTED** in the snippets.
            2. If the user provided a broad topic like "{last_user_msg}", extract 3 REAL interview questions related to that {last_user_msg}. 
               - RULES: Verbatim quotes only. Must cite URL.
               - If the user doesn't have knowledge on that topic from their resume, draft ideal answers using ONLY their resume data.
            
            🚨 CRITICAL RULES FOR CITATION:
            1. **VERBATIM ONLY:** You can only list a question if you can find the *exact sentence* in the text.
               - ❌ Bad: Snippet says "asked about SQL joins" -> You write "What are types of joins?" (Hallucination)
               - ✅ Good: Snippet says "Interviewer asked: 'Explain Left Join vs Inner Join'" -> You write "Explain Left Join vs Inner Join".
            
            2. **IF NO EXACT QUOTES FOUND:** - Do NOT invent questions.
               - Instead, summarize the *topics* mentioned in the snippet.
               - Format: "Topic: [Topic Name] (Exact question not listed)"
            
            3. **SOURCE MATCHING:** The URL you list MUST be the one where that specific text came from.


            OUTPUT FORMAT:
            ### 🎯 Question [1/2/3]
            **❓ Real Question:** [Insert Technical/Behavioral Question found in text]
            
            **🔗 Source:** [Insert Exact URL]

            **✅ Ideal Answer:** [First-person answer drafting using ONLY resume data]

            **💡 The Logic:** [Why this answer is good - not first person perspective]
            
            CONTEXT:
            {context}
            """
            new_depth = 0
        
        else:
            # === PATH C: OFF-TOPIC GUARDRAIL ===
            system_prompt = f"""
            You are AURA, a specialized Career Architect Agent.
            
            Your ONLY purpose is to help candidates prepare for technical interviews at {company}.
            
            TASK:
            The user has asked an off-topic question: "{last_user_msg}".
            You must politely REFUSE to answer it.
            
            RULES:
            - Do NOT answer the question (e.g. do NOT explain who the actor is).
            - Do NOT provide general knowledge.
            - Redirect the user back to their Resume or Interview Prep.
            
            OUTPUT FORMAT:
            ### ⛔ Out of Scope
            **Reason:** My knowledge base is strictly limited to your **Resume** and **{company} Interview Patterns**.
            
            **Action:** I cannot answer general knowledge questions. Please ask me to:
            1. Explain a project from your resume.
            2. Find real interview questions for {company}.
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
                instruction = "🛑 TOPIC SWITCH: You have asked enough about this. STRICTLY ask a NEW, UNRELATED question about a DIFFERENT skill in the resume."
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