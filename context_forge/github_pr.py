import logging

logger = logging.getLogger(__name__)


def create_pull_request(repo, branch_name: str, pr_title: str, pr_body: str) -> str:
    logger.info(f"Creating pull request for branch: {branch_name}")
    existing_prs = repo.get_pulls(state='open', head=f"{repo.owner.login}:{branch_name}")
    for pr in existing_prs:
        if pr.head.ref == branch_name:
            logger.info(f"Existing PR found: {pr.html_url}")
            return pr.html_url

    pr = repo.create_pull(title=pr_title, body=pr_body, head=branch_name, base='main')
    logger.info(f"Created new PR: {pr.html_url}")
    return pr.html_url
