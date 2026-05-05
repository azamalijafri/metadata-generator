import os
import logging
from dotenv import load_dotenv
from metadata_framework import MetadataFramework
from github_automation import automate_github_pr

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting metadata generation and GitHub PR automation")

    DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
    DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
    MODEL_SERVING_ENDPOINT_NAME = os.getenv("MODEL_SERVING_ENDPOINT_NAME")
    MODEL_SERVING_TOKEN = os.getenv("MODEL_SERVING_TOKEN")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "databricks").lower()
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO_NAME = os.getenv("REPO_NAME")

    if not REPO_NAME:
        raise ValueError("REPO_NAME is not set. Expected format: github-username/repo-name")
    if "/" not in REPO_NAME:
        raise ValueError(f"REPO_NAME '{REPO_NAME}' is invalid. Expected format: github-username/repo-name")
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN is not set")

    logger.info(f"Configuration loaded - Repository: {REPO_NAME}, LLM Provider: {LLM_PROVIDER}")

    downstream_views = [
        "workspace.default.customer_summary",
        "workspace.default.order_summary"
    ]

    logger.info(f"Initializing MetadataFramework with {LLM_PROVIDER.upper()} provider")
    mf = MetadataFramework(
        DATABRICKS_HOST,
        DATABRICKS_TOKEN,
        llm_provider=LLM_PROVIDER,
        model_serving_token=MODEL_SERVING_TOKEN,
        model_serving_endpoint_name=MODEL_SERVING_ENDPOINT_NAME,
        groq_api_key=GROQ_API_KEY,
        groq_model=GROQ_MODEL
    )

    logger.info(f"Generating descriptions for {len(downstream_views)} views with lineage")
    result = mf.run(downstream_views)

    descriptions = result.get('descriptions', {})
    for view_name, desc in descriptions.items():
        logger.info(f"Generated Description for {view_name}: %s", desc)

    pr_metadata = result.get('pr_metadata', {})
    logger.info("Starting GitHub PR automation")

    pr_url = automate_github_pr(
        descriptions,
        pr_metadata,
        REPO_NAME,
        GITHUB_TOKEN
    )

    logger.info(f"Process completed successfully - PR URL: {pr_url}")

if __name__ == "__main__":
    main()
