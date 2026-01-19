from agent import TaskAgent

def main():
    print("Task Breakdown & Execution Agent")
    print("--------------------------------")
    
    agent = TaskAgent()
    
    while True:
        objective = input("\nEnter your objective (or 'quit' to exit): ")
        if objective.lower() in ['quit', 'exit']:
            break
            
        try:
            agent.run(objective)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
