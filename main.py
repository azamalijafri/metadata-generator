import os
import logging
from metadata_framework import MetadataFramework
from github_automation import automate_github_pr
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting metadata generation and GitHub PR automation")

    # Load environment variables
    DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
    DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
    MODEL_SERVING_ENDPOINT = os.getenv("MODEL_SERVING_ENDPOINT")
    MODEL_SERVING_TOKEN = os.getenv("MODEL_SERVING_TOKEN")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO_DIR = os.getenv("REPO_DIR")
    REPO_NAME = os.getenv("REPO_NAME")

    logger.info(f"Configuration loaded - Repository: {REPO_NAME}")

    upstream_tables = [
        "workspace.default.raw_customers",
        "workspace.default.raw_orders"
    ]
    downstream_table = "workspace.default.customer_summary"

    # Extract actual table name for SQL filename
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

    logger.info("Initializing MetadataFramework with Databricks connection")
    mf = MetadataFramework(
        DATABRICKS_HOST,
        DATABRICKS_TOKEN,
        model_serving_token=MODEL_SERVING_TOKEN,
        model_endpoint=MODEL_SERVING_ENDPOINT
    )

    logger.info("Generating table description and PR metadata using LLM")
    result = mf.run(upstream_tables, downstream_table, sql_query)

    # Extract description and PR metadata from JSON result
    description = result.get('description', 'No description generated')
    pr_metadata = result.get('pr_metadata', {})

    logger.info("Description generated successfully")
    logger.info("Starting GitHub PR automation")

    # Pass the downstream table info for JSON entry
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
