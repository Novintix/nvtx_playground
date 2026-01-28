# Document RAG API Documentation

This API provides endpoints for uploading documents, querying them using Retrieval-Augmented Generation (RAG), and managing collections in a Chroma vector database.

The API runs on `http://localhost:3300` by default.

## Endpoints

### 1. Upload Documents
**Endpoint:** `POST http://localhost:3300/upload`

**Description:** Upload documents to be processed and indexed in the vector database. Supports PDF, DOCX, TXT, PNG, and JPEG files.

**Sample Input:**
```
Content-Type: multipart/form-data

files: [file1.pdf, file2.docx] (multiple files)
collection_name: "my_collection" (optional, defaults to "default")
```

**Sample Output (Expected):**
```json
{
  "message": "Successfully processed 2 documents",
  "results": [
    {
      "filename": "file1.pdf",
      "status": "success",
      "chunks_added": 15,
      "document_ids": ["id1", "id2", ..., "id15"]
    },
    {
      "filename": "file2.docx",
      "status": "success",
      "chunks_added": 8,
      "document_ids": ["id16", "id17", ..., "id23"]
    }
  ]
}
```

### 2. Query Documents
**Endpoint:** `POST http://localhost:3300/query`

**Description:** Query the RAG system with a question about the documents. Returns an answer generated based on the relevant document chunks.

**Sample Input:**
```json
{
  "query": "What is the main topic of the uploaded documents?",
  "collection_name": "my_collection",
  "top_k": 5
}
```

**Sample Output (Expected):**
```json
{
  "answer": "The main topic of the uploaded documents is machine learning and artificial intelligence, covering topics such as neural networks, deep learning algorithms, and their applications in various domains.",
  "sources": [
    {
      "content": "Machine learning is a subset of artificial intelligence...",
      "metadata": {
        "source": "document1.pdf",
        "page": 1
      },
      "score": 0.95
    },
    {
      "content": "Deep learning algorithms have revolutionized...",
      "metadata": {
        "source": "document2.pdf",
        "page": 3
      },
      "score": 0.89
    }
  ]
}
```

### 3. List Collections
**Endpoint:** `GET http://localhost:3300/collections`

**Description:** List all available collections in the vector database.

**Sample Input:** None

**Sample Output (Expected):**
```json
{
  "collections": [
    "default",
    "my_collection",
    "n8n_workflows"
  ]
}
```

### 4. Delete Collection
**Endpoint:** `DELETE http://localhost:3300/collections/{collection_name}`

**Description:** Delete a collection from the vector database.

**Sample Input:** None (collection name in URL path)

**Sample Output (Expected):**
```json
{
  "message": "Collection 'my_collection' deleted successfully"
}
```

### 5. Upload Workflows
**Endpoint:** `POST http://localhost:3300/upload_workflows`

**Description:** Upload all JSON files from the 'workflows' directory to a specified Chroma collection.

**Sample Input:**
```
Content-Type: multipart/form-data

collection_name: "n8n_workflows" (optional, defaults to "n8n_workflows")
```

**Sample Output (Expected):**
```json
{
  "message": "Processed 25 workflow files",
  "results": [
    {
      "filename": "0001_Telegram_Schedule_Automation_Scheduled.json",
      "status": "success",
      "chunks_added": 12,
      "document_ids": ["wf1", "wf2", ..., "wf12"]
    },
    {
      "filename": "0002_Manual_Totp_Automation_Triggered.json",
      "status": "success",
      "chunks_added": 8,
      "document_ids": ["wf13", "wf14", ..., "wf20"]
    },
    ...
  ]
}
```