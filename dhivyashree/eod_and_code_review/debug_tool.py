import requests
import base64

def get_file_content(repo_full_name: str, file_path: str):
    """Fetches the content of a specific file from a GitHub repository."""
    url = f"https://api.github.com/repos/{repo_full_name}/contents/{file_path}"
    print(f"DEBUG: Requesting URL: {url}")
    response = requests.get(url)
    
    print(f"DEBUG: Status Code: {response.status_code}")
    print(f"DEBUG: Response Text: {response.text}")

    if response.status_code == 200:
        data = response.json()
        if 'content' not in data:
            print(f"Error: No content found for {file_path}. It might be a directory or too large.")
            return
        
        # try:
        #     content = base64.b64decode(data['content']).decode('utf-8')
        #     print(f"Content of {file_path}:\n\n{content[:100]}...") # Print first 100 chars
        # except Exception as e:
        #     print(f"Error decoding file content: {e}")
    else:
        print(f"Error fetching file: {response.status_code} - {response.text}")

if __name__ == "__main__":
    # Test with the repo/file that failed
    repo = "Dhivyashree1208/eod_code_review"
    file = "agent.py" # Based on the user request trace
    get_file_content(repo, file)
