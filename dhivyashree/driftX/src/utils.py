import PyPDF2
import io

def read_file_content(uploaded_file) -> str:
    """
    Reads content from a Streamlit UploadedFile (PDF or Text).
    """
    if uploaded_file.type == "application/pdf":
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    else:
        # Assume text/plain or similar
        return uploaded_file.getvalue().decode("utf-8")
