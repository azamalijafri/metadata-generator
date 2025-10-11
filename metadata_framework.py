import os
import json
import logging
from git import Repo
from github import Github

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_description_in_json(description, file_path, table_info):
    """Update or append table description in JSON file"""
    logger.info(f"Updating JSON description file: {file_path}")
    
    try:
        # Read existing JSON file
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded existing JSON with {len(data)} entries")
        else:
            data = []
            logger.info("Creating new JSON file")

        # Extract schema and table name from table_info (e.g., "workspace.default.customer_summary")
        parts = table_info.split('.')
        schema = parts[1] if len(parts) >= 2 else "default"
        table = parts[2] if len(parts) >= 3 else parts[-1]

        # Create new entry
        new_entry = {
            "schema": schema,
            "table": table,
            "description": description
        }

        # Check if entry already exists and update, otherwise append
        entry_found = False
        for i, entry in enumerate(data):
            if entry.get("schema") == schema and entry.get("table") == table:
                data[i] = new_entry
                entry_found = True
                logger.info(f"Updated existing entry for {schema}.{table}")
                break

        if not entry_found:
            data.append(new_entry)
            logger.info(f"Added new entry for {schema}.{table}")

        # Write updated JSON back to file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"JSON file updated successfully with {len(data)} total entries")

    except Exception as e:
        logger.error(f"Error updating JSON file {file_path}: {e}")
        raise

def create_and_push_branch(repo_dir, branch_name, file_path, commit_msg, description, table_info):
    logger.info(f"Creating and pushing branch: {branch_name}")
    try:
        repo = Repo(repo_dir)
        origin = repo.remote(name='origin')

        # Branch checkout or create
        if branch_name in repo.heads:
            logger.info(f"Checking out existing branch: {branch_name}")
            repo.heads[branch_name].checkout()
        else:
            logger.info(f"Creating new branch: {branch_name}")
            repo.git.checkout('HEAD', b=branch_name)

        # Update JSON file with new description
        update_description_in_json(description, file_path, table_info)

        # Add and commit changes
        repo.git.add(file_path)
        repo.index.commit(commit_msg)
        logger.info(f"Changes committed with message: {commit_msg}")

        # Update feature branch with latest main to avoid conflicts
        logger.info("Fetching latest changes from main branch")
        origin.fetch()
        try:
            repo.git.merge('origin/main')
            logger.info("Successfully merged latest main branch changes")
        except Exception as merge_error:
            logger.warning(f"Merge warning (continuing): {merge_error}")

        # Push branch
        origin.push(branch_name)
        logger.info(f"Branch {branch_name} pushed to remote successfully")

    except Exception as e:
        logger.error(f"Error in branch creation/push: {e}")
        raise

def create_pull_request(repo_name, branch_name, pr_title, pr_body, github_token):
    logger.info(f"Creating pull request for branch: {branch_name}")
    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)

        # Check for existing open PR from this branch
        prs = repo.get_pulls(state='open', head=f"{repo.owner.login}:{branch_name}")

        for pr in prs:
            if pr.head.ref == branch_name:
                logger.info(f"Existing PR found: {pr.html_url}")
                return pr.html_url

        # Create new PR
        pr = repo.create_pull(title=pr_title, body=pr_body, head=branch_name, base='main')
        logger.info(f"New PR created successfully: {pr.html_url}")
        return pr.html_url

    except Exception as e:
        logger.error(f"Error creating pull request: {e}")
        raise

def automate_github_pr(description, pr_metadata, repo_dir, repo_name, github_token, table_info):
    logger.info("Starting GitHub PR automation")
    try:
        file_path = os.path.join(repo_dir, 'configs/downstream_table_description.json')  # Changed to .json
        
        # Use LLM-generated metadata or fallback to defaults
        branch_name = pr_metadata.get('branch_name', 'update-downstream-table-desc')
        commit_msg = pr_metadata.get('commit_message', 'Auto-update downstream table metadata description')
        pr_title = pr_metadata.get('title', 'Update downstream table metadata description')
        pr_body = pr_metadata.get('body', 'This PR updates the description for the downstream table generated by automation.')

        logger.info(f"Using branch name: {branch_name}")
        logger.info(f"Using PR title: {pr_title}")

        create_and_push_branch(repo_dir, branch_name, file_path, commit_msg, description, table_info)
        pr_url = create_pull_request(repo_name, branch_name, pr_title, pr_body, github_token)

        logger.info(f"GitHub PR automation completed - PR URL: {pr_url}")
        return pr_url

    except Exception as e:
        logger.error(f"Error in GitHub PR automation: {e}")
        raise
