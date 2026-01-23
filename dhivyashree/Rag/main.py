import sys
import argparse
from Rag.agent.workflow import ContextAgent

def main():
    parser = argparse.ArgumentParser(description="Group Chat Context Reconstruction Agent")
    parser.add_argument("query", type=str, help="The natural language query (e.g., 'What happened last week?')")
    args = parser.parse_args()
    
    # Ensure Unicode characters (emojis) print correctly on Windows
    sys.stdout.reconfigure(encoding='utf-8')

    try:
        agent = ContextAgent()
        response = agent.run(args.query)
        print("\n" + "="*50)
        print("AGENT RESPONSE")
        print("="*50 + "\n")
        print(response)
    except Exception as e:
        print(f"Error running agent: {e}")

if __name__ == "__main__":
    main()
