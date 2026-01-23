from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


def create_rag_chain(llm, vector_db):
    """
    Creates a RAG chain that retrieves relevant documents
    and generates answers using the LLM.
    """
    
    # Create a retriever from the vector store
    retriever = vector_db.as_retriever(search_kwargs={"k": 4})
    
    # Define the prompt template
    prompt = ChatPromptTemplate.from_template(
        """Answer the question based only on the following context. 
        If you don't know the answer, say that you don't know.

        Context: {context}

        Question: {query}

        Answer:"""
    )
    
    # Format documents function
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    # Create the RAG chain using LCEL
    rag_chain = (
        {
            "context": retriever | format_docs,
            "query": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # Wrap it to return a dict with result and source_documents
    def invoke_with_sources(query):
        docs = retriever.invoke(query)
        result = rag_chain.invoke(query)
        return {
            "result": result,
            "source_documents": docs
        }
    
    # Return a callable object that mimics the old chain interface
    class RAGChainWrapper:
        def __init__(self, chain_func):
            self.chain_func = chain_func
        
        def __call__(self, inputs):
            return self.chain_func(inputs["query"])
    
    return RAGChainWrapper(invoke_with_sources)
