from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState
from src.retrieval import get_retriever
from src.tools import web_search_tool

# Initialize LLM (Ensure you use the one you set up: Groq or Gemini)
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.5)

def retrieve_node(state: AgentState):
    """
    Fetches Resume chunks + Web Search Results (with links).
    """
    query = state["messages"][-1].content
    company = state["target_company"]
    
    # 1. Internal RAG (Resume)
    resume_context = ""
    retriever = get_retriever()
    if retriever:
        docs = retriever.invoke(query)
        resume_context = "\n".join([doc.page_content for doc in docs])
    
    # 2. External Search (Company Questions)
    web_context = "No specific company info found."
    if company and len(company) > 2:
        try:
            # We specifically ask for "Interview Questions" to get listicles/blogs
            search_query = f"latest {company} technical interview questions and experience 2025 2026"
            web_context = web_search_tool.invoke(search_query)
        except Exception:
            web_context = "Search failed."

    combined_context = f"""
    === RESUME CONTEXT (STRICT GROUNDING) ===
    {resume_context}
    
    === WEB SEARCH RESULTS (SOURCE DATA) ===
    {web_context}
    """
    
    return {"retrieved_docs": combined_context}


def generate_node(state: AgentState):
    mode = state["mode"]
    context = state["retrieved_docs"]
    messages = state["messages"]
    company = state["target_company"]
    
    if "trainer" in mode.lower():
        # --- NEW TRAINER PROMPT ---
        system_prompt = f"""
        You are AURA, an Expert Interview Coach.
        
        TASK:
        1. Analyze the [WEB SEARCH RESULTS] to find REAL interview questions asked by {company}.
        2. Select the top 3 most relevant technical questions.
        3. For each question, craft a "Winning Answer" based ONLY on the user's [RESUME CONTEXT].
        
        STRICT RULES:
        - Do NOT invent skills. If the resume doesn't have the answer, admit it.
        - The answer must use the STAR format (Situation, Task, Action, Result) from the resume projects.
        
        OUTPUT FORMAT (Use this exact structure):
        
        ### 🎯 Top Interview Questions for {company}
        
        **Question 1:** [Question Text]
        **Your Winning Answer:** [Drafted answer citing specific resume project]
        
        **Question 2:** [Question Text]
        **Your Winning Answer:** [Drafted answer citing specific resume project]
        
        **Question 3:** [Question Text]
        **Your Winning Answer:** [Drafted answer citing specific resume project]
        
        ---
        ### 🔗 Sources
        #1 [Source Name/URL from Search]
        #2 [Source Name/URL from Search]
        #3 [Source Name/URL from Search]
        
        CONTEXT DATA:
        {context}
        """
    else:
        # Mode 2: The Strict Interviewer
        system_prompt = f"""
        You are a Senior Technical Recruiter at {company}.
        You are conducting a hard technical interview.
        
        GOAL: Test the candidate's depth.
        
        INSTRUCTIONS:
        1. Look at the user's latest answer.
        2. CRITIQUE it based on the [RESUME CONTEXT]. Did they lie? Did they miss details?
        3. Ask a follow-up question that digs deeper into their specific tech stack (e.g., "Why did you use LangGraph instead of Zapier?").
        4. Be professional, concise, and neutral. Do not help them.

        STRICT GROUNDING RULE:
        - Do NOT assume technologies (like Flutter or React) unless they are explicitly present in the [RESUME CONTEXT] or the User's latest message.
        - If you don't see a technology in the context, ask the user what stack they used; do not guess.
        
        CONTEXT:
        {context}
        """

    # Create the prompt chain
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}")
    ])
    
    chain = prompt | llm
    
    # Run the chain
    response = chain.invoke({"messages": messages})
    
    return {"messages": [response]}