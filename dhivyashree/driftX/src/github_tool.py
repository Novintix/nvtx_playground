from github import Github
import os
from dotenv import load_dotenv

load_dotenv()

def get_github_client():
    token = os.getenv("GITHUB_TOKEN")
    return Github(token) if token else Github()

def fetch_repo_structure(repo_url):
    """
    Fetches the file structure of a public GitHub repository.
    repo_url example: "https://github.com/streamlit/streamlit"
    """
    try:
        g = get_github_client()
        # Extract "owner/repo" from URL
        repo_name = "/".join(repo_url.split("/")[-2:])
        repo = g.get_repo(repo_name)
        
        contents = repo.get_contents("")
        file_tree = []
        
        skip_dirs = {".git", "node_modules", "venv", "__pycache__", "dist", "build", ".next", "coverage"}
        
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                if file_content.name in skip_dirs:
                    continue
                try:
                    contents.extend(repo.get_contents(file_content.path))
                except Exception:
                    pass # Skip if access denied or empty
            else:
                file_tree.append(file_content.path)
                
        return file_tree[:50] # Limit to 50 files to avoid context explosion
    except Exception as e:
        return f"Error fetching repo: {str(e)}"

def fetch_file_content(repo_url, file_path):
    """
    Fetches raw content of a specific file.
    """
    try:
        g = get_github_client()
        repo_name = "/".join(repo_url.split("/")[-2:])
        repo = g.get_repo(repo_name)
        file_content = repo.get_contents(file_path)
        return file_content.decoded_content.decode("utf-8")
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"
