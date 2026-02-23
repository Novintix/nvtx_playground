import os
import shutil
import subprocess
import tempfile

def clone_repo(repo_url):
    """
    Clones a git repository to a temporary directory.
    Returns the path to the closed directory.
    """
    temp_dir = tempfile.mkdtemp()
    try:
        subprocess.check_call(["git", "clone", repo_url, temp_dir])
        return temp_dir
    except subprocess.CalledProcessError as e:
        shutil.rmtree(temp_dir)
        raise Exception(f"Failed to clone repository: {e}")

import stat

def on_rm_error(func, path, exc_info):
    """
    Error handler for shutil.rmtree.
    If the error is due to an access error (read only file),
    it attempts to add write permission and then retries.
    If the error is for another reason it re-raises the error.
    """
    # Is the error an access error?
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)

def cleanup_repo(path):
    """
    Removes the temporary directory.
    """
    if os.path.exists(path):
        # On Windows, git files are often read-only. We need a handler.
        shutil.rmtree(path, onerror=on_rm_error)
