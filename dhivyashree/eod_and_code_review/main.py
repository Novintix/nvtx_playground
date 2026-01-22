import os
import sys
from dotenv import load_dotenv

# Load env vars before importing other modules that might use them (like agent.py)
load_dotenv()

from langchain_core.messages import HumanMessage
from agent import workflow
from db import get_checkpointer

def main():

    # Setup persistence
    print("Connecting to MongoDB...")
    try:
        checkpointer = get_checkpointer()
        print("Connected to MongoDB.")
    except Exception as e:
        print(f"Warning: Could not connect to MongoDB. Running without persistence. Error: {e}")
        checkpointer = None

    # Compile the graph
    app = workflow.compile(checkpointer=checkpointer)

    # Config for the thread - simulating a persistent session 
    # In a real app, this ID would come from a user session
    import uuid
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("--- Context-Aware Agent Started ---")
    print("Agent is ready.")
    print("-" * 50)
    
    # Interactive Loop
    while True:
        try:
            user_input = input("\nUse Input: ").strip()
            
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting agent. Goodbye!")
                break
                
            if not user_input:
                continue

            inputs = {"messages": [HumanMessage(content=user_input)]}
            
            # Processing Loop with Retry Logic
            import time
            from google.api_core.exceptions import ResourceExhausted

            max_retries = 3
            retry_delay = 60 # seconds
            
            success = False
            for attempt in range(max_retries):
                try:
                    print("\nProcessing...")
                    for event in app.stream(inputs, config=config):
                        for key, value in event.items():
                            if key == "agent":
                                 if "messages" in value:
                                    last_msg = value["messages"][-1]
                                    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                                         for tc in last_msg.tool_calls:
                                             print(f"  [Action] Calling tool: {tc['name']}...")
                                    elif hasattr(last_msg, 'content') and last_msg.content:
                                         # Print normal agent response if it's not a tool call or EOD
                                         # This is important for conversational turns (e.g. asking "Which repo?")
                                         if "Reasoning:" not in last_msg.content and "EOD Update" not in last_msg.content:
                                              print(f"\nAssistant: {last_msg.content}")

                            
                            elif key == "tools":
                                messages = value.get("messages", [])
                                for msg in messages:
                                    if hasattr(msg, 'content') and msg.content:
                                        # Check if this is file content and truncate it for display
                                        content_str = str(msg.content)
                                        if content_str.startswith("Content of ") and len(content_str) > 200:
                                            # Extract the first line (filename)
                                            first_line = content_str.split('\n')[0]
                                            print(f"\n[Tool Output]:\n{first_line}\n...(File content hidden separately for brevity)...\n")
                                        else:
                                            print(f"\n[Tool Output]:\n{msg.content}\n")
                                print("  [Action] Tool execution completed.")

                            elif key == "eod_generator":
                                if "eod_update" in value:
                                    print("\n" + "="*40)
                                    print("       END OF DAY UPDATE")
                                    print("="*40)
                                    print(value['eod_update'])
                                    print("="*40 + "\n")
                    
                    success = True
                    break # Success, exit retry loop

                except ResourceExhausted:
                    print(f"\n[Warning] API Rate Limit Exceeded (429). Waiting {retry_delay} seconds before retrying (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(retry_delay)
                    print("Retrying...")
                except Exception as e:
                    print(f"An error occurred during execution: {e}")
                    import traceback
                    traceback.print_exc()
                    break
            
            if not success:
                 print("Failed to process request after retries.")

        except KeyboardInterrupt:
            print("\nExiting agent. Goodbye!")
            break
        except Exception as e:
             print(f"\nCritical Error in input loop: {e}")
             break

if __name__ == "__main__":
    main()
