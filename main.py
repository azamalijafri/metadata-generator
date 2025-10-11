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
    """
    Load configuration, read SQL, generate table description and PR metadata via LLM,
    then create or update a GitHub PR with the results.
    """
    logger.info("Starting metadata generation and GitHub PR automation")

    # Environment configuration
    DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
    DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
    MODEL_SERVING_ENDPOINT = os.getenv("MODEL_SERVING_ENDPOINT")
    MODEL_SERVING_TOKEN = os.getenv("MODEL_SERVING_TOKEN")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "databricks").lower()
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO_DIR = os.getenv("REPO_DIR")
    REPO_NAME = os.getenv("REPO_NAME")

    logger.info(f"Configuration loaded - Repository: {REPO_NAME}, LLM Provider: {LLM_PROVIDER}")

    upstream_tables = [
        "workspace.default.raw_customers",
        "workspace.default.raw_orders"
    ]
    
    downstream_table = "workspace.default.customer_summary"

    actual_table_name = downstream_table.split('.')[-1]
    sql_file_path = os.path.join(os.getcwd(), "sql", f"{actual_table_name}.sql")
    logger.info(f"Loading SQL from file: {sql_file_path}")

    try:
        with open(sql_file_path, 'r') as sql_file:
            sql_query = sql_file.read()
        logger.info("SQL query loaded successfully")
    except Exception as e:
        logger.error(f"Failed to read SQL file {sql_file_path}: {e}")
        raise

    logger.info(f"Initializing MetadataFramework with {LLM_PROVIDER.upper()} provider")
    mf = MetadataFramework(
        DATABRICKS_HOST,
        DATABRICKS_TOKEN,
        llm_provider=LLM_PROVIDER,
        model_serving_token=MODEL_SERVING_TOKEN,
        model_endpoint=MODEL_SERVING_ENDPOINT,
        groq_api_key=GROQ_API_KEY,
        groq_model=GROQ_MODEL
    )

    logger.info("Generating table description and PR metadata using LLM")
    result = mf.run(upstream_tables, downstream_table, sql_query)

    description = result.get('description', 'No description generated')
    logger.info("Generated Description: %s", description)

    pr_metadata = result.get('pr_metadata', {})
    logger.info("Starting GitHub PR automation")

    pr_url = automate_github_pr(
        description,
        pr_metadata,
        REPO_DIR,
        REPO_NAME,
        GITHUB_TOKEN,
        downstream_table
    )

    logger.info(f"Process completed successfully - PR URL: {pr_url}")

if __name__ == "__main__":
    main()
