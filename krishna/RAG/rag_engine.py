import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Google Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

class RAGEngine:
    def __init__(self):
        # Initialize ChromaDB client
        self.persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
        os.makedirs(self.persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(allow_reset=True)
        )
        
        # Initialize the embedding model (BAAI/bge-large-en)
        print("Loading SentenceTransformer model...")
        try:
            self.embedding_model = SentenceTransformer("BAAI/bge-large-en")
            print("SentenceTransformer model loaded successfully!")
        except Exception as e:
            print(f"Error loading SentenceTransformer: {e}")
            print("Falling back to a simpler model...")
            try:
                self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                print("Fallback model loaded successfully!")
            except Exception as e2:
                print(f"Error loading fallback model: {e2}")
                raise Exception(f"Could not load any embedding model. Original error: {e}")
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")
    
    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        return self.embedding_model.encode(texts).tolist()
    
    def _get_or_create_collection(self, collection_name: str):
        """Get or create a ChromaDB collection."""
        try:
            collection = self.client.get_collection(name=collection_name)
        except:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return collection
    
    def add_documents(self, documents: List[Dict[str, Any]], collection_name: str = "default") -> List[str]:
        """
        Add documents to the vector database.
        
        Args:
            documents: List of document chunks with text and metadata
            collection_name: Name of the collection to add documents to
            
        Returns:
            List of document IDs
        """
        print(f"Adding {len(documents)} documents to collection '{collection_name}'")
        
        if not documents:
            print("ERROR: Documents list is empty!")
            return []
        
        try:
            collection = self._get_or_create_collection(collection_name)
            
            # Extract document IDs, texts, and metadata
            ids = [doc["id"] for doc in documents]
            texts = [doc["text"] for doc in documents]
            metadatas = [doc["metadata"] for doc in documents]
            
            print(f"Processing {len(texts)} text chunks...")
            
            # Generate embeddings
            embeddings = self._get_embeddings(texts)
            print(f"Generated {len(embeddings)} embeddings")
            
            # Add documents to the collection
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            
            print(f"Successfully added {len(ids)} documents to ChromaDB")
            return ids
            
        except Exception as e:
            print(f"Error in add_documents: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def query(self, query_text: str, collection_name: str = "default", top_k: int = 5) -> Dict[str, Any]:
        """
        Query the RAG system with a question.
        
        Args:
            query_text: The question to ask
            collection_name: Name of the collection to query
            top_k: Number of most relevant chunks to retrieve
            
        Returns:
            Dictionary with answer and relevant chunks
        """
        try:
            collection = self._get_or_create_collection(collection_name)
            
            # Generate embedding for the query
            query_embedding = self._get_embeddings([query_text])[0]
            
            # Query the collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Extract relevant chunks and their metadata
            relevant_chunks = []
            context_text = ""
            
            if results["documents"] and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]
                    
                    # Add to context text
                    context_text += f"\nDocument: {metadata['source']}, Chunk {metadata['chunk_index'] + 1}/{metadata['total_chunks']}\n"
                    context_text += f"{doc}\n"
                    
                    # Add to relevant chunks
                    relevant_chunks.append({
                        "text": doc,
                        "metadata": metadata,
                        "relevance_score": 1 - distance  # Convert distance to similarity score
                    })
            
            # Generate answer using Gemini
            if context_text:
                prompt = f"""
                You are an AI assistant that answers questions based on the provided context.
                Answer the following question using ONLY the information from the provided context.
                If the context doesn't contain the information needed to answer the question, say "I don't have enough information to answer this question."
                
                Context:
                {context_text}
                
                Question: {query_text}
                
                Answer:
                """
                
                response = self.model.generate_content(prompt)
                answer = response.text
            else:
                answer = "I don't have enough information to answer this question. Please upload relevant documents first."
            
            # Return the answer and relevant chunks
            return {
                "query": query_text,
                "answer": answer,
                "relevant_chunks": relevant_chunks
            }
            
        except Exception as e:
            return {
                "query": query_text,
                "answer": f"Error generating answer: {str(e)}",
                "relevant_chunks": []
            }
    
    def list_collections(self) -> List[str]:
        """List all available collections in the vector database."""
        collections = self.client.list_collections()
        return [collection.name for collection in collections]
    
    def delete_collection(self, collection_name: str):
        """Delete a collection from the vector database."""
        self.client.delete_collection(collection_name) 
        