import os
import logging
from metadata_framework import MetadataFramework
from github_automation import automate_github_pr
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
    DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
    MODEL_SERVING_ENDPOINT = os.getenv("MODEL_SERVING_ENDPOINT")
    MODEL_SERVING_TOKEN = os.getenv("MODEL_SERVING_TOKEN")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO_DIR = os.getenv("REPO_DIR")
    REPO_NAME = os.getenv("REPO_NAME")

    # upstream_tables = [
    #     "workspace.default.raw_customers",
    #     "workspace.default.raw_orders"
    # ]
    # downstream_table = "workspace.default.customer_summary"
    # sql_query = """
    #     SELECT 
    #         c.customer_id,
    #         c.customer_name,
    #         COUNT(o.order_id) AS total_orders,
    #         SUM(o.order_amount) AS total_spent,
    #         MAX(o.order_date) AS last_order_date
    #     FROM workspace.default.raw_customers c
    #     LEFT JOIN workspace.default.raw_orders o ON c.customer_id = o.customer_id
    #     GROUP BY c.customer_id, c.customer_name
    # """

    # mf = MetadataFramework(
    #     DATABRICKS_HOST, 
    #     DATABRICKS_TOKEN, 
    #     model_serving_token=MODEL_SERVING_TOKEN, 
    #     model_endpoint=MODEL_SERVING_ENDPOINT
    # )
    # description = mf.run(upstream_tables, downstream_table, sql_query)

    # logger.info("Generated Description:\n%s", description)

    description = """This table contains a summary of customer activities, including total orders and spending. It is derived from raw customer and order data through SQL aggregation. The primary purpose is to provide insights into customer behavior for business analysis."""

    automate_github_pr(description, REPO_DIR, REPO_NAME, GITHUB_TOKEN)

if __name__ == "__main__":
    main()
