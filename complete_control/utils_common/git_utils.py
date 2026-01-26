import subprocess
from pathlib import Path

import structlog

_log: structlog.BoundLogger = structlog.get_logger("[utils]")


def get_git_commit_hash(repo_path: str | Path) -> str:
    repo_path = Path(repo_path)
    if not repo_path.exists():
        _log.error(f"Directory not found: {repo_path}")
        return "dir_not_found"

    try:
        process = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        _log.error(f"Error getting git hash for {repo_path}: {e.stderr.strip()}")
        return "unknown"
    except FileNotFoundError:
        _log.error("Git command not found. Ensure git is installed and in PATH.")
        return "git_not_found"
