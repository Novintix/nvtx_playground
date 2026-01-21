import os
import requests
import base64
from langchain_core.tools import tool

@tool
def list_github_repos(username: str) -> str:
    """Lists public repositories for a given GitHub username."""
    url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(url)
    
    if response.status_code == 200:
        repos = response.json()
        if not repos:
            return f"No public repositories found for user '{username}'."
        
    # Sort by pushed_at (descending) and limit to top 10
        repos.sort(key=lambda x: x.get("pushed_at", ""), reverse=True)
        repos = repos[:10]
        
        result = f"Top 10 Repositories for {username} (by recent activity):\n"
        for repo in repos:
            result += f"- {repo['full_name']} (Default branch: {repo['default_branch']})\n"
        return result
    else:
        return f"Error fetching repos: {response.status_code} - {response.text}"

@tool
def get_github_commits(repo_full_name: str) -> str:
    """Fetches recent commits from a specific GitHub repository (e.g., 'owner/repo')."""
    url = f"https://api.github.com/repos/{repo_full_name}/commits"
    response = requests.get(url)
    
    if response.status_code == 200:
        commits = response.json()
        # Limit to last 5 commits
        recent_commits = commits[:5]
        
        result = f"Recent Commits for {repo_full_name}:\n"
        for commit in recent_commits:
            sha = commit['sha'][:7]
            message = commit['commit']['message']
            author = commit['commit']['author']['name']
            date = commit['commit']['author']['date']
            result += f"Commit: [{sha}] ({author}, {date})\nMessage: {message}\n---\n"
        return result
    else:
        return f"Error fetching commits: {response.status_code} - {response.text}"

@tool
def get_task_logs(task_id: str) -> str:
    """Simulated tool to get task logs."""
    return f"Logs for task {task_id}:\n- [INFO] Task started\n- [INFO] Processing data\n- [SUCCESS] Task completed successfully."

@tool
def list_repo_files(repo_full_name: str, path: str = "") -> str:
    """Lists files and directories in a specific path of a GitHub repository (e.g., 'owner/repo')."""
    url = f"https://api.github.com/repos/{repo_full_name}/contents/{path}"
    response = requests.get(url)
    
    if response.status_code == 200:
        items = response.json()
        if not isinstance(items, list):
            # It's a file, not a directory
            return f"Path '{path}' points to a file, not a directory. Use `get_file_content` to read it."
            
        result = f"Contents of {repo_full_name}/{path}:\n"
        for item in items:
            type_icon = "[DIR]" if item['type'] == 'dir' else "[FILE]"
            result += f"{type_icon} {item['name']}\n"
        return result
    else:
        return f"Error listing files: {response.status_code} - {response.text}"

@tool
def get_file_content(repo_full_name: str, file_path: str) -> str:
    """Fetches the content of a specific file from a GitHub repository. 
    args:
        repo_full_name: "owner/repo"
        file_path: "path/to/file.py" (relative to root, NO leading slash)
    """
    # Clean up file path
    file_path = file_path.strip().lstrip('/')
    
    url = f"https://api.github.com/repos/{repo_full_name}/contents/{file_path}"
    print(f"DEBUG: get_file_content fetching: {url}") # Visible in console
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if 'content' not in data:
            return f"Error: No content found for {file_path}. It might be a directory or too large."
        
        try:
            content = base64.b64decode(data['content']).decode('utf-8')
            return f"Content of {file_path}:\n\n{content}"
        except Exception as e:
            return f"Error decoding file content: {e}"
    else:
        return f"Error fetching file: {response.status_code} - {response.text}"

@tool
def save_daily_standup(plan: str) -> str:
    """Saves the user's daily standup (intentions/goals for the day)."""
    return f"Daily standup saved: {plan}"
