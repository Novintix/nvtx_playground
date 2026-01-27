# Group Chat Context Reconstruction Agent

This project implements an AI agent that reconstructs conversation context for users who join a group chat late. It uses RAG (Retrieval Augmented Generation) with MongoDB to filter messages by date, reconstruct threads, and provide a human-centric summary.

## Features

- **Context Reconstruction**: Rebuilds conversation history from disjointed messages.
- **Temporal Filtering**: Retrieves messages within specific date ranges.
- **Metadata-First RAG**: Prioritizes structure (threads, reply chains) over pure vector similarity for accurate context.
- **Human-Centric Output**: Generates summaries identifying participants, decisions, and action items.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    - Update `config.py` with your MongoDB URI.
    - Set `OPENAI_API_KEY` or equivalent in your environment variables.

3.  **Seed Data**:
    ```bash
    python -m rag_chat_agent.database.seeder
    ```

4.  **Run Agent**:
    ```bash
    python -m rag_chat_agent.main "What happened between Jan 20 and Jan 23?"
    ```

## Requirements

- Python 3.9+
- MongoDB
