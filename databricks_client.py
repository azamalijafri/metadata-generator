from databricks.sdk import WorkspaceClient
import logging

logger = logging.getLogger(__name__)


def create_workspace_client(host: str, token: str) -> WorkspaceClient:
    logger.info("Connecting to Databricks workspace")
    return WorkspaceClient(host=host, token=token)
