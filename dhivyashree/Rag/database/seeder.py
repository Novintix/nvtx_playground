from Rag.database.connection import get_collection, init_db
from datetime import datetime

SAMPLE_MESSAGES = [
    {
        "group_id": "backend-team",
        "message_id": "msg_1001",
        "user_name": "Alice",
        "role": "lead",
        "message_text": "Hey team, we need to discuss the login latency issues reported by QA.",
        "timestamp": "2026-01-20T09:00:00Z",
        "date": "2026-01-20",
        "thread_id": "latency_fix_01",
        "reply_to": None,
        "topic": "performance",
        "message_type": "discussion",
        "action_item": None,
        "mentions": ["@channel"],
        "tags": ["latency", "login"],
        "importance": "high"
    },
    {
        "group_id": "backend-team",
        "message_id": "msg_1002",
        "user_name": "Bob",
        "role": "backend-dev",
        "message_text": "I noticed it too. It seems to happen when the user has many notifications.",
        "timestamp": "2026-01-20T09:05:00Z",
        "date": "2026-01-20",
        "thread_id": "latency_fix_01",
        "reply_to": "msg_1001",
        "topic": "performance",
        "message_type": "discussion",
        "action_item": None,
        "mentions": [],
        "tags": ["latency"],
        "importance": "medium"
    },
    {
        "group_id": "backend-team",
        "message_id": "msg_1003",
        "user_name": "Priya",
        "role": "qa",
        "message_text": "Confirmed. It spikes to 2s for users with > 100 notifications.",
        "timestamp": "2026-01-20T09:10:00Z",
        "date": "2026-01-20",
        "thread_id": "latency_fix_01",
        "reply_to": "msg_1002",
        "topic": "performance",
        "message_type": "issue",
        "action_item": None,
        "mentions": ["Bob"],
        "tags": ["latency", "metrics"],
        "importance": "high"
    },
    {
        "group_id": "backend-team",
        "message_id": "msg_1004",
        "user_name": "Alice",
        "role": "lead",
        "message_text": "we need to optimize the notification fetch query.",
        "timestamp": "2026-01-20T09:15:00Z",
        "date": "2026-01-20",
        "thread_id": "latency_fix_01",
        "reply_to": "msg_1003",
        "topic": "performance",
        "message_type": "decision",
        "action_item": "Optimize notification fetch query",
        "mentions": ["Bob"],
        "tags": ["db", "optimization"],
        "importance": "high"
    },
    {
        "group_id": "backend-team",
        "message_id": "msg_1005",
        "user_name": "Bob",
        "role": "backend-dev",
        "message_text": "I'll take this. I can add an index on userId and isRead status.",
        "timestamp": "2026-01-20T09:20:00Z",
        "date": "2026-01-20",
        "thread_id": "latency_fix_01",
        "reply_to": "msg_1004",
        "topic": "performance",
        "message_type": "commitment",
        "action_item": "Add DB index for notifications",
        "mentions": [],
        "tags": ["db"],
        "importance": "medium"
    },
    # Day 2 - Another topic
    {
        "group_id": "backend-team",
        "message_id": "msg_2001",
        "user_name": "Dave",
        "role": "devops",
        "message_text": "Heads up, we are migrating the primary database to the new cluster tonight.",
        "timestamp": "2026-01-21T16:00:00Z",
        "date": "2026-01-21",
        "thread_id": "migration_01",
        "reply_to": None,
        "topic": "infrastructure",
        "message_type": "announcement",
        "action_item": None,
        "mentions": ["@channel"],
        "tags": ["migration", "downtime"],
        "importance": "critical"
    },
    {
        "group_id": "backend-team",
        "message_id": "msg_2002",
        "user_name": "Alice",
        "role": "lead",
        "message_text": "What is the expected downtime?",
        "timestamp": "2026-01-21T16:05:00Z",
        "date": "2026-01-21",
        "thread_id": "migration_01",
        "reply_to": "msg_2001",
        "topic": "infrastructure",
        "message_type": "question",
        "action_item": None,
        "mentions": ["Dave"],
        "tags": ["migration"],
        "importance": "high"
    },
    {
        "group_id": "backend-team",
        "message_id": "msg_2003",
        "user_name": "Dave",
        "role": "devops",
        "message_text": "About 15 minutes. Scheduled for 2 AM UTC.",
        "timestamp": "2026-01-21T16:10:00Z",
        "date": "2026-01-21",
        "thread_id": "migration_01",
        "reply_to": "msg_2002",
        "topic": "infrastructure",
        "message_type": "answer",
        "action_item": None,
        "mentions": [],
        "tags": ["migration"],
        "importance": "medium"
    },
    # Day 3 - Follow up on Latency
    {
        "group_id": "backend-team",
        "message_id": "msg_3001",
        "user_name": "Bob",
        "role": "backend-dev",
        "message_text": "The index is added. Latency dropped to 200ms.",
        "timestamp": "2026-01-22T10:00:00Z",
        "date": "2026-01-22",
        "thread_id": "latency_fix_01",
        "reply_to": "msg_1005",
        "topic": "performance",
        "message_type": "update",
        "action_item": None,
        "mentions": ["Alice", "Priya"],
        "tags": ["fix", "latency"],
        "importance": "high"
    },
    {
        "group_id": "backend-team",
        "message_id": "msg_3002",
        "user_name": "Priya",
        "role": "qa",
        "message_text": "Verified on staging. Looks good.",
        "timestamp": "2026-01-22T10:30:00Z",
        "date": "2026-01-22",
        "thread_id": "latency_fix_01",
        "reply_to": "msg_3001",
        "topic": "performance",
        "message_type": "verification",
        "action_item": None,
        "mentions": ["Bob"],
        "tags": ["qa"],
        "importance": "medium"
    },
     {
        "group_id": "backend-team",
        "message_id": "msg_3003",
        "user_name": "Alice",
        "role": "lead",
        "message_text": "Great. Deploy to prod today.",
        "timestamp": "2026-01-22T11:00:00Z",
        "date": "2026-01-22",
        "thread_id": "latency_fix_01",
        "reply_to": "msg_3002",
        "topic": "performance",
        "message_type": "decision",
        "action_item": "Deploy fix to prod",
        "mentions": ["Dave"],
        "tags": ["deployment"],
        "importance": "high"
    }
]

def seed():
    init_db()
    collection = get_collection()
    # Clear existing data for clean slate (optional, good for dev)
    collection.delete_many({})
    
    # Add embeddings placeholder
    for msg in SAMPLE_MESSAGES:
        msg["embedding"] = [] # In real app, we'd generate this here
        
    collection.insert_many(SAMPLE_MESSAGES)
    print(f"Seeded {len(SAMPLE_MESSAGES)} messages.")

if __name__ == "__main__":
    seed()
