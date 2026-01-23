import json
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from Rag.config import GROQ_API_KEY, MODEL_NAME
from Rag.agent.prompts import DATE_EXTRACTION_PROMPT, CONTEXT_RECONSTRUCTION_PROMPT
from Rag.database.repository import retrieve_messages

class ContextAgent:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in config or environment.")
        
        self.llm = ChatGroq(model=MODEL_NAME, temperature=0, api_key=GROQ_API_KEY)
        self.date_chain = DATE_EXTRACTION_PROMPT | self.llm | StrOutputParser()
        self.summary_chain = CONTEXT_RECONSTRUCTION_PROMPT | self.llm | StrOutputParser()

    def run(self, query: str):
        # Step 1: Extract Dates
        print(f"Analyzing query: '{query}'...")
        try:
            date_json_str = self.date_chain.invoke({"query": query})
            # Clean up potential markdown code blocks if LLM adds them
            date_json_str = date_json_str.replace("```json", "").replace("```", "").strip()
            date_range = json.loads(date_json_str)
            start_date = date_range.get("start_date")
            end_date = date_range.get("end_date")
            print(f"identified Date Range: {start_date} to {end_date}")
        except Exception as e:
            print(f"Error extracting dates: {e}")
            return "Could not determine date range from query."

        # Step 2: Retrieve Messages
        if not start_date or not end_date:
            return "Please specify a valid date range."
            
        messages = retrieve_messages(start_date, end_date)
        
        if not messages:
            return f"No messages found between {start_date} and {end_date}."
            
        print(f"Retrieved {len(messages)} messages. reconstructing context...")

        # Step 3: Format Context
        context_str = ""
        for msg in messages:
            timestamp = msg.get("timestamp", "")
            user = msg.get("user_name", "Unknown")
            role = msg.get("role", "")
            text = msg.get("message_text", "")
            msg_type = msg.get("message_type", "message")
            
            context_str += f"[{timestamp}] {user} ({role}) [{msg_type}]: {text}\n"

        # Step 4: Generate Summary
        result = self.summary_chain.invoke({"context": context_str})
        return result
