import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
import datetime

load_dotenv()

# Initialize the LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

# Create the search tool
search_tool = TavilySearch(
    api_key=os.getenv("TAVILY_API_KEY")
)

# Create custom tool for getting current time
@tool
def get_system_time(time_format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Returns the current system time in the specified format.
    
    Args:
        time_format: The datetime format string (default: "%Y-%m-%d %H:%M:%S")
    
    Returns:
        str: The current system time as a formatted string
    """
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime(time_format)           
    return formatted_time

# Create custom calculator tool
@tool
def calculate_days_between(date1: str, date2: str) -> str:
    """Calculate the number of days between two dates.
    
    Args:
        date1: First date in YYYY-MM-DD format
        date2: Second date in YYYY-MM-DD format
    
    Returns:
        str: Number of days between the two dates
    """
    try:
        d1 = datetime.datetime.strptime(date1, "%Y-%m-%d")
        d2 = datetime.datetime.strptime(date2, "%Y-%m-%d")
        difference = abs((d2 - d1).days)
        return f"{difference} days"
    except Exception as e:
        return f"Error calculating days: {str(e)}"

# List of tools
tools = [search_tool, get_system_time, calculate_days_between]

# System prompt with REACT pattern instructions
system_prompt = """You are a helpful AI assistant that uses the REACT (Reasoning and Acting) pattern.

Available tools:
- tavily_search: Search the web for current information
- get_system_time: Get the current date and time
- calculate_days_between: Calculate days between two dates (format: YYYY-MM-DD)

REACT Pattern Instructions:
1. THINK: Analyze what the user is asking
2. ACT: Use the appropriate tools to gather information
3. OBSERVE: Examine the results from the tools
4. REASON: Combine the information logically
5. RESPOND: Provide a clear, accurate answer

Always show your reasoning process when using tools."""

# Create the agent
agent = create_agent(
    model=llm, 
    tools=tools, 
    system_prompt=system_prompt
)

def run_agent(user_question: str):
    """Run the agent with a user question and display the result."""
    print("\n" + "="*60)
    print(f"QUESTION: {user_question}")
    print("="*60)
    print("\n🤔 Agent is thinking and working...\n")
    
    try:
        # Invoke the agent
        result = agent.invoke({
            "messages": [{"role": "user", "content": user_question}]
        })
        
        # Display all messages (shows the REACT reasoning process)
        if result and 'messages' in result:
            print("="*60)
            print("REASONING PROCESS:")
            print("="*60)
            
            for idx, msg in enumerate(result['messages'], 1):
                if hasattr(msg, 'content') and msg.content:
                    role = getattr(msg, 'type', 'message')
                    print(f"\nStep {idx} [{role}]:")
                    print(msg.content)
                    print("-" * 60)
            
            # Extract final answer
            final_message = result['messages'][-1]
            print("\n" + "="*60)
            print("FINAL ANSWER:")
            print("="*60)
            if hasattr(final_message, 'content'):
                print(final_message.content)
            else:
                print(final_message)
        else:
            print(result)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n" + "="*60 + "\n")

def main():
    """Main function to run the interactive REACT agent."""
    print("\n" + "🤖 " + "="*58)
    print("   REACT PATTERN AGENT - Built with LangChain")
    print("="*60)
    print("\nAvailable Tools:")
    print("  • Web Search (Tavily)")
    print("  • System Time")
    print("  • Date Calculator")
    print("\nType 'quit' or 'exit' to stop\n")
    print("="*60)
    
    # Example questions for first-time users
    example_questions = [
        "What is LangGraph?",
        "When was SpaceX's last launch and how many days ago was that?",
        "What's the current time?",
        "What are the latest developments in AI?"
    ]
    
    print("\n💡 Example questions you can ask:")
    for i, q in enumerate(example_questions, 1):
        print(f"   {i}. {q}")
    print()
    
    while True:
        try:
            # Get user input
            user_input = input("Your question: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye! Thanks for using the REACT agent.\n")
                break
            
            # Skip empty inputs
            if not user_input:
                print("❌ Please enter a question.\n")
                continue
            
            # Run the agent
            run_agent(user_input)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for using the REACT agent.\n")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}\n")

if __name__ == "__main__":
    main()