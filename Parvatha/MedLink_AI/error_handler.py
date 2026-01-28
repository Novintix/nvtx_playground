# error_handler.py

def handle_error(error: Exception):
    error_msg = str(error)

    if "NCBI" in error_msg or "Entrez" in error_msg:
        return "⚠️ Unable to reach NCBI servers. Please check your internet connection or API key."

    if "FAISS" in error_msg:
        return "⚠️ Vector database error. Try rebuilding the index."

    if "CUDA" in error_msg or "torch" in error_msg:
        return "⚠️ Model loading issue. Try running on CPU or reducing batch size."

    return f"⚠️ Unexpected error occurred: {error_msg}"
