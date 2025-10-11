import os
import json
import logging
from git import Repo
from github import Github

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def update_description_in_json(description: str, file_path: str, table_info: str):
    """
    Append or update a table description in a JSON array stored at file_path.

    Args:
        description: The description text to write.
        file_path: Path to the JSON file.
        table_info: Fully qualified table name (e.g., "workspace.default.table").
    """
    logger.info(f"Updating JSON description file: {file_path}")
    data = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded existing JSON with {len(data)} entries")

    parts = table_info.split('.')
    schema = parts[1] if len(parts) >= 2 else "default"
    table = parts[2] if len(parts) >= 3 else parts[-1]
    new_entry = {"schema": schema, "table": table, "description": description}

    for i, entry in enumerate(data):
        if entry.get("schema") == schema and entry.get("table") == table:
            data[i] = new_entry
            logger.info(f"Updated existing entry for {schema}.{table}")
            break
    else:
        data.append(new_entry)
        logger.info(f"Added new entry for {schema}.{table}")

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"JSON file updated successfully with {len(data)} entries")

def create_and_push_branch(repo_dir: str, branch_name: str, file_path: str,
                           commit_msg: str, description: str, table_info: str):
    """
    Create or checkout a git branch, update the JSON, commit changes, and push.

    Args:
        repo_dir: Root directory of the git repository.
        branch_name: Name of the branch to create or update.
        file_path: Path to the JSON file within the repo.
        commit_msg: Commit message for the change.
        description: Table description text.
        table_info: Fully qualified table name for JSON update.
    """
    logger.info(f"Creating or updating branch: {branch_name}")
    repo = Repo(repo_dir)
    origin = repo.remote(name='origin')

    if branch_name in repo.heads:
        repo.heads[branch_name].checkout()
        logger.info(f"Checked out existing branch: {branch_name}")
    else:
        repo.git.checkout('HEAD', b=branch_name)
        logger.info(f"Created new branch: {branch_name}")

    update_description_in_json(description, file_path, table_info)

    repo.git.add(file_path)
    repo.index.commit(commit_msg)
    logger.info(f"Committed changes: {commit_msg}")

    origin.fetch()
    try:
        repo.git.merge('origin/main')
        logger.info("Merged latest main into branch")
    except Exception as merge_error:
        logger.warning(f"Merge warning (continuing): {merge_error}")

    origin.push(branch_name)
    logger.info(f"Pushed branch {branch_name} to origin")

def create_pull_request(repo_name: str, branch_name: str,
                        pr_title: str, pr_body: str, github_token: str) -> str:
    """
    Create a GitHub pull request or return existing one for the branch.

    Args:
        repo_name: GitHub repo identifier (e.g., "user/repo").
        branch_name: Head branch for the PR.
        pr_title: Title of the pull request.
        pr_body: Body text of the pull request.
        github_token: Personal access token for GitHub.

    Returns:
        URL of the created or existing pull request.
    """
    logger.info(f"Creating pull request for branch: {branch_name}")
    gh = Github(github_token)
    repo = gh.get_repo(repo_name)

    existing_prs = repo.get_pulls(state='open', head=f"{repo.owner.login}:{branch_name}")
    for pr in existing_prs:
        if pr.head.ref == branch_name:
            logger.info(f"Existing PR found: {pr.html_url}")
            return pr.html_url

    pr = repo.create_pull(title=pr_title, body=pr_body, head=branch_name, base='main')
    logger.info(f"Created new PR: {pr.html_url}")
    return pr.html_url

def automate_github_pr(description: str, pr_metadata: dict,
                       repo_dir: str, repo_name: str, github_token: str,
                       table_info: str) -> str:
    """
    Orchestrate branch creation, JSON update, and pull request creation.

    Args:
        description: Table description text.
        pr_metadata: Dictionary with keys branch_name, title, body, commit_message.
        repo_dir: Root directory of the git repository.
        repo_name: GitHub repo identifier.
        github_token: Personal access token for GitHub.
        table_info: Fully qualified table name for JSON update.

    Returns:
        URL of the created or updated pull request.
    """
    file_path = os.path.join(repo_dir, 'configs', 'table_metadata.json')
    branch_name = pr_metadata.get('branch_name', 'update-downstream-table-desc')
    commit_msg = pr_metadata.get('commit_message', 'Auto-update downstream table metadata description')
    pr_title = pr_metadata.get('title', 'Update downstream table metadata description')
    pr_body = pr_metadata.get('body', 'Update downstream table description via automation')

    logger.info(f"Automating PR on branch: {branch_name}")
    create_and_push_branch(repo_dir, branch_name, file_path, commit_msg, description, table_info)
    pr_url = create_pull_request(repo_name, branch_name, pr_title, pr_body, github_token)
    logger.info(f"Pull request URL: {pr_url}")
    return pr_url
