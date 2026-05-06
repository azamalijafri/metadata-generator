import os
import logging
from dotenv import load_dotenv
from context_forge import ContextForge, automate_github_pr

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting metadata generation and GitHub PR automation")

    downstream_views = [
        "workspace.default.customer_summary",
        "workspace.default.order_summary"
    ]

    cf = ContextForge(
        host=os.getenv("DATABRICKS_HOST"),
        databricks_token=os.getenv("DATABRICKS_TOKEN"),
        llm_provider=os.getenv("LLM_PROVIDER", "databricks").lower(),
        model_serving_token=os.getenv("MODEL_SERVING_TOKEN"),
        model_serving_endpoint_name=os.getenv("MODEL_SERVING_ENDPOINT_NAME"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
        groq_model=os.getenv("GROQ_MODEL", "llama3-8b-8192"),
        warehouse_http_path=os.getenv("WAREHOUSE_HTTP_PATH")
    )

    result = cf.run(downstream_views)

    pr_url = automate_github_pr(
        descriptions=result["descriptions"],
        branch_name=result["branch_name"],
        commit_msg=result["commit_message"],
        pr_title=result["pr_title"],
        pr_body=result["pr_body"],
        repo_name=os.getenv("REPO_NAME"),
        github_token=os.getenv("GITHUB_TOKEN")
    )

    logger.info(f"Process completed - PR URL: {pr_url}")

if __name__ == "__main__":
    main()
