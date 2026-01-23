from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FakeEmbeddings


def _load_policy_text(path: str = "data/policy.txt") -> str:
    """Lightweight loader for the policy file (no heavy LangChain loaders)."""
    print("Loading documents...")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    print("✓ Loaded 1 document")
    return text


def _simple_char_split(
    text: str,
    chunk_size: int = 200,
    chunk_overlap: int = 20,
) -> list[str]:
    """Very small, fast character-based splitter (no external deps)."""
    print("Splitting documents...")
    chunks: list[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap

    print(f"✓ Split into {len(chunks)} chunks")
    return chunks


def create_vectorstore():
    text = _load_policy_text()
    chunks = _simple_char_split(text)

    # Use a very lightweight, fast embedding implementation so startup is quick.
    print("Loading lightweight embeddings (FakeEmbeddings)...")
    embeddings = FakeEmbeddings(size=384)
    print("✓ Embeddings ready")

    print("Creating vectorstore...")
    vectorstore = FAISS.from_texts(chunks, embeddings)
    print("✓ Vectorstore created")
    return vectorstore
