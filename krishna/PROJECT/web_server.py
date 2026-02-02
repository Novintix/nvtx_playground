import os
import json
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Import the main agent system
from main_G import build_main_graph, notion_client, filesystem_client
from langchain_core.messages import HumanMessage

app = FastAPI(title="Multi-Agent MCP UI Server")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to MCP endpoints JSON
MCP_JSON_PATH = os.path.join(os.path.dirname(__file__), "mcp_endpoints.json")

# Global agent graph
agent_graph = None
graph_config = {"configurable": {"thread_id": "web_ui_thread"}}


class MCPEndpoint(BaseModel):
    name: str
    transport: str = "streamable_http"
    url: str
    description: str = ""


class ChatMessage(BaseModel):
    message: str


@app.on_event("startup")
async def startup_event():
    """Initialize the agent graph on startup"""
    global agent_graph
    try:
        # Initialize MCP clients
        from main_G import _notion_tools, _filesystem_tools, _notion_subgraph, _filesystem_subgraph
        import main_G
        
        main_G._notion_tools = await notion_client.get_tools()
        main_G._filesystem_tools = await filesystem_client.get_tools()
        
        # Import the creation functions to cache subgraphs
        from main_G import create_notion_subgraph, create_filesystem_subgraph
        main_G._notion_subgraph = await create_notion_subgraph()
        main_G._filesystem_subgraph = await create_filesystem_subgraph()
        
        agent_graph = build_main_graph()
        print("✅ Multi-agent system initialized successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize MCP clients: {e}")
        print("The system will still work for dynamic MCP endpoints")


@app.get("/")
async def serve_ui():
    """Serve the HTML UI"""
    ui_path = os.path.join(os.path.dirname(__file__), "ui.html")
    return FileResponse(ui_path)


@app.get("/mcps")
async def get_mcps():
    """Get all configured MCP endpoints"""
    if not os.path.exists(MCP_JSON_PATH):
        return {}
    
    with open(MCP_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/mcps/add")
async def add_mcp(endpoint: MCPEndpoint):
    """Add a new MCP endpoint"""
    # Load existing endpoints
    if os.path.exists(MCP_JSON_PATH):
        with open(MCP_JSON_PATH, "r", encoding="utf-8") as f:
            endpoints = json.load(f)
    else:
        endpoints = {}
    
    # Check if name already exists
    if endpoint.name in endpoints:
        raise HTTPException(status_code=400, detail=f"MCP '{endpoint.name}' already exists")
    
    # Add new endpoint
    endpoints[endpoint.name] = {
        "transport": endpoint.transport,
        "url": endpoint.url,
        "description": endpoint.description
    }
    
    # Save to file
    with open(MCP_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(endpoints, f, indent=2)
    
    return {"status": "success", "message": f"MCP '{endpoint.name}' added successfully"}


@app.delete("/mcps/remove/{name}")
async def remove_mcp(name: str):
    """Remove an MCP endpoint"""
    if not os.path.exists(MCP_JSON_PATH):
        raise HTTPException(status_code=404, detail="No MCP endpoints configured")
    
    with open(MCP_JSON_PATH, "r", encoding="utf-8") as f:
        endpoints = json.load(f)
    
    if name not in endpoints:
        raise HTTPException(status_code=404, detail=f"MCP '{name}' not found")
    
    # Remove endpoint
    del endpoints[name]
    
    # Save to file
    with open(MCP_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(endpoints, f, indent=2)
    
    # Clear cached dynamic subgraph if exists
    import main_G
    if name in main_G._dynamic_subgraphs:
        del main_G._dynamic_subgraphs[name]
    if name in main_G._dynamic_tools:
        del main_G._dynamic_tools[name]
    
    return {"status": "success", "message": f"MCP '{name}' removed successfully"}


@app.post("/chat")
async def chat(msg: ChatMessage):
    """Send a message to the agent"""
    if agent_graph is None:
        raise HTTPException(status_code=503, detail="Agent system not initialized")
    
    try:
        print("\n" + "="*80)
        print(f"🔵 NEW USER MESSAGE: {msg.message}")
        print("="*80)
        
        # Collect all events
        events = []
        async for event in agent_graph.astream(
            {"messages": [HumanMessage(content=msg.message)]},
            config=graph_config
        ):
            events.append(event)
            event_keys = list(event.keys())
            print(f"📦 Event received: {event_keys}")
            
            # Print details of each event
            for key, value in event.items():
                if key == "__end__":
                    print(f"   └─ [__end__] Final state received")
                elif key == "supervisor":
                    next_agent = value.get('next_agent', 'N/A')
                    task = value.get('current_task', 'N/A')
                    print(f"   └─ [supervisor] next_agent={next_agent}, task={task[:50]}...")
                else:
                    print(f"   └─ [{key}] event")
        
        print(f"\n📊 Total events received: {len(events)}")
        
        # Try to extract response from events
        final_response = None
        
        # Method 1: Look for __end__ event
        for event in reversed(events):
            if "__end__" in event:
                final_state = event["__end__"]
                messages = final_state.get("messages", [])
                
                print(f"\n📝 Found __end__ event with {len(messages)} messages")
                print("-" * 80)
                
                if messages:
                    # Print ALL messages for debugging
                    for i, msg_obj in enumerate(messages):
                        msg_type = type(msg_obj).__name__
                        content_preview = str(msg_obj.content)[:150].replace('\n', ' ')
                        print(f"\n  Message {i+1}/{len(messages)}:")
                        print(f"    Type: {msg_type}")
                        print(f"    Content: {content_preview}...")
                        if hasattr(msg_obj, 'name') and msg_obj.name:
                            print(f"    Name: {msg_obj.name}")
                    
                    print("\n" + "-" * 80)
                    
                    # Collect all assistant/agent responses (skip user messages)
                    responses = []
                    for msg_obj in messages:
                        msg_type = type(msg_obj).__name__
                        
                        # Skip HumanMessage, include everything else
                        if msg_type != "HumanMessage":
                            responses.append(f"[{msg_type}] {msg_obj.content}")
                    
                    if responses:
                        final_response = "\n\n".join(responses)
                    else:
                        final_response = str(messages[-1].content)
                
                break
        
        # Method 2: If no __end__ event, check for supervisor FINISH
        if not final_response:
            print("\n⚠️ No __end__ event found, checking for supervisor FINISH...")
            for event in reversed(events):
                if "supervisor" in event:
                    supervisor_data = event["supervisor"]
                    next_agent = supervisor_data.get("next_agent", "")
                    task = supervisor_data.get("current_task", "")
                    
                    if next_agent == "FINISH" and task:
                        print(f"\n✅ Found FINISH from supervisor!")
                        print(f"   Task/Answer: {task}")
                        final_response = task
                        break
        
        if final_response:
            print(f"\n✅ RETURNING RESPONSE:")
            print(final_response)
            print("=" * 80 + "\n")
            return {"response": final_response}
        
        print("\n❌ NO RESPONSE GENERATED - couldn't extract response")
        print("=" * 80 + "\n")
        return {"response": "No response generated - couldn't extract response"}
        
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR in chat: {e}")
        print(traceback.format_exc())
        print("=" * 80 + "\n")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("🚀 Starting Multi-Agent MCP UI Server...")
    print("📍 Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000)
