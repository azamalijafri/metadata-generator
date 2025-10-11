import os
import logging
from metadata_framework import MetadataFramework
from github_automation import automate_github_pr
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
    
    pr_url = automate_github_pr(description, pr_metadata, REPO_DIR, REPO_NAME, GITHUB_TOKEN)
    
    logger.info(f"Process completed successfully - PR URL: {pr_url}")

if __name__ == "__main__":
    main()
