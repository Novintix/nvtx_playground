import os
import requests
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
            message = commit['commit']['message'].split('\n')[0]
            author = commit['commit']['author']['name']
            date = commit['commit']['author']['date']
            result += f"- [{sha}] {message} ({author}, {date})\n"
        return result
    else:
        return f"Error fetching commits: {response.status_code} - {response.text}"

@tool
def get_task_logs(task_id: str) -> str:
    """Simulated tool to get task logs."""
    # In a real app, this would fetch from a DB or log file
    return f"Logs for task {task_id}:\n- [INFO] Task started\n- [INFO] Processing data\n- [SUCCESS] Task completed successfully."
