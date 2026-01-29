"""
AI Summarization service using Groq
"""
import os
from groq import Groq


def summarize_slack_messages(messages: list[dict]) -> str:
    """
    Summarize Slack messages using Groq AI
    
    Args:
        messages: List of message dicts with 'text', 'user', 'timestamp'
    
    Returns:
        Summary text
    """
    if not messages:
        return "No messages found to summarize."
    
    # Format messages for AI
    messages_text = "\n".join([
        f"- {msg.get('text', '')}"
        for msg in messages
    ])
    
    # Check if Groq API key is available
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        # Return simple summary without AI
        return f"Found {len(messages)} messages. AI summarization unavailable (no GROQ_API_KEY set)."
    
    try:
        client = Groq(api_key=api_key)
        
        prompt = f"""Summarize the following Slack messages into a concise summary (2-3 sentences max):

{messages_text}

Summary:"""
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes Slack conversations concisely."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        summary = completion.choices[0].message.content.strip()
        return summary
        
    except Exception as e:
        # Fallback if AI fails
        return f"Found {len(messages)} messages. Error summarizing: {str(e)}"
