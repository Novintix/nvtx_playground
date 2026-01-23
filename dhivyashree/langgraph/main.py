import os
from dotenv import load_dotenv
# Load environment variables before other imports
load_dotenv()

from graph import compile_graph
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run a Debate-Driven Decision Agent")
    parser.add_argument("topic", type=str, help="The topic to debate")
    args = parser.parse_args()
    
    topic = args.topic
    print(f"Starting debate on topic: {topic}\n" + "-"*50)
    
    # Initialize graph
    graph = compile_graph()
    
    # Initial state
    initial_state = {"topic": topic, "messages": []}
    
    # Run the graph
    events = graph.invoke(initial_state)
    
    # Output results
    print(f"\n[Pro Agent Argument]:\n{events['pro_argument']}\n")
    print(f"-"*50)
    print(f"\n[Con Agent Argument]:\n{events['con_argument']}\n")
    print(f"-"*50)
    print(f"\n[Judge Verdict]:\n{events['verdict']}\n")

if __name__ == "__main__":
    main()
