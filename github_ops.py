import base64
import logging
from github.GithubException import GithubException

logger = logging.getLogger(__name__)


def get_file_content(repo, file_path: str) -> tuple:
    logger.info(f"Fetching file content for: {file_path}")
    content = repo.get_contents(file_path, ref="main")
    decoded = base64.b64decode(content.content).decode("utf-8")
    return decoded, content.sha


def create_file(repo, file_path: str, content: str, commit_msg: str, branch: str) -> str:
    logger.info(f"Creating file {file_path} on branch {branch}")
    result = repo.create_file(
        path=file_path,
        message=commit_msg,
        content=content,
        branch=branch
    )
    return result["commit"].sha


def update_file(repo, file_path: str, content: str, sha: str, commit_msg: str, branch: str) -> str:
    logger.info(f"Updating file {file_path} on branch {branch}")
    result = repo.update_file(
        path=file_path,
        message=commit_msg,
        content=content,
        sha=sha,
        branch=branch
    )
    return result["commit"].sha


def create_branch(repo, branch_name: str) -> None:
    logger.info(f"Creating branch: {branch_name}")
    main_ref = repo.get_git_ref("heads/main")
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_ref.object.sha)
    logger.info(f"Branch {branch_name} created from main")


def create_branch_safe(repo, branch_name: str) -> None:
    try:
        create_branch(repo, branch_name)
    except GithubException as e:
        if "already exists" in str(e).lower() or "reference already exists" in str(e).lower():
            logger.warning(f"Branch {branch_name} already exists, continuing")
        else:
            raise
