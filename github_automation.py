import logging
from github import Github
from github_ops import get_file_content, update_file, create_file, create_branch_safe
from github_pr import create_pull_request
from github_metadata import update_descriptions_in_json

logger = logging.getLogger(__name__)


def automate_github_pr(descriptions: dict, branch_name: str, commit_msg: str,
                       pr_title: str, pr_body: str,
                       repo_name: str, github_token: str) -> str:
    file_path = "configs/table_metadata.json"

    logger.info(f"Automating PR on branch: {branch_name} for {len(descriptions)} views")

    gh = Github(github_token)
    try:
        repo = gh.get_repo(repo_name)
    except Exception as e:
        raise RuntimeError(f"Failed to access repo '{repo_name}'. Check REPO_NAME format and GITHUB_TOKEN access. Error: {e}") from e

    create_branch_safe(repo, branch_name)

    try:
        current_content, sha = get_file_content(repo, file_path)
    except Exception:
        logger.info(f"File {file_path} does not exist on main, will create it")
        current_content, sha = None, None

    updated_content = update_descriptions_in_json(descriptions, current_content or "")

    if sha:
        update_file(repo, file_path, updated_content, sha, commit_msg, branch_name)
    else:
        create_file(repo, file_path, updated_content, commit_msg, branch_name)

    pr_url = create_pull_request(repo, branch_name, pr_title, pr_body)
    logger.info(f"Pull request URL: {pr_url}")
    return pr_url
