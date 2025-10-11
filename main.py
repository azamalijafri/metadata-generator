import os
import logging
from metadata_framework import MetadataFramework
from github_automation import automate_github_pr
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting main function")
    
    # Load environment variables
    DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
    DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
    MODEL_SERVING_ENDPOINT = os.getenv("MODEL_SERVING_ENDPOINT")
    MODEL_SERVING_TOKEN = os.getenv("MODEL_SERVING_TOKEN")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO_DIR = os.getenv("REPO_DIR")
    REPO_NAME = os.getenv("REPO_NAME")
    
    logger.debug(f"Environment variables loaded - REPO_DIR: {REPO_DIR}, REPO_NAME: {REPO_NAME}")

    upstream_tables = [
        "workspace.default.raw_customers",
        "workspace.default.raw_orders"
    ]
    downstream_table = "workspace.default.customer_summary"
    sql_query = """
        SELECT 
            c.customer_id,
            c.customer_name,
            COUNT(o.order_id) AS total_orders,
            SUM(o.order_amount) AS total_spent,
            MAX(o.order_date) AS last_order_date
        FROM workspace.default.raw_customers c
        LEFT JOIN workspace.default.raw_orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_id, c.customer_name
    """

    logger.info("Initializing MetadataFramework")
    mf = MetadataFramework(
        DATABRICKS_HOST, 
        DATABRICKS_TOKEN, 
        model_serving_token=MODEL_SERVING_TOKEN, 
        model_endpoint=MODEL_SERVING_ENDPOINT
    )
    
    logger.info("Running metadata framework to generate description and PR metadata")
    result = mf.run(upstream_tables, downstream_table, sql_query)
    
    logger.info("Generated Result:\n%s", result)
    
    # Extract description and PR metadata from JSON result
    description = result.get('description', 'No description generated')
    pr_metadata = result.get('pr_metadata', {})
    
    logger.info("Starting GitHub PR automation")
    automate_github_pr(description, pr_metadata, REPO_DIR, REPO_NAME, GITHUB_TOKEN)
    logger.info("Main function completed")

if __name__ == "__main__":
    main()
