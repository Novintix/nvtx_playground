from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_and_chunk_pdf(pdf_path: str):
    """
    Loads a PDF, splits it into chunks,
    and attaches section + page metadata.
    """

    loader = UnstructuredPDFLoader(pdf_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )

    final_chunks = []

    for doc in documents:
        page_number = doc.metadata.get("page", "NA")
        section_title = doc.metadata.get("title", "Unknown Section")

        chunks = splitter.split_documents([doc])

        for chunk in chunks:
            chunk.metadata = {
                "section": section_title,
                "page": page_number
            }
            final_chunks.append(chunk)

    return final_chunks
