import logging
from databricks.sdk import WorkspaceClient
from databricks import sql

logger = logging.getLogger(__name__)


def fetch_table_metadata(db_client: WorkspaceClient, table_name: str):
    logger.info(f"Fetching metadata for table: {table_name}")
    try:
        metadata = db_client.tables.get(full_name=table_name)
        logger.info(f"Retrieved metadata for {table_name}")
        return metadata
    except Exception as e:
        logger.error(f"Failed to fetch metadata for {table_name}: {e}")
        raise


def fetch_sample_rows(host: str, http_path: str, token: str, table_name: str, limit: int = 3) -> list:
    logger.info(f"Fetching {limit} sample rows for: {table_name}")
    try:
        with sql.connect(
            server_hostname=host.replace("https://", ""),
            http_path=http_path,
            access_token=token
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = []
                for row in cursor.fetchall():
                    rows.append(dict(zip(columns, row)))
                return rows
    except Exception as e:
        logger.warning(f"Failed to fetch sample rows for {table_name}: {e}")
        return []


def fetch_view_context(db_client: WorkspaceClient, downstream_table_name: str) -> tuple:
    logger.info(f"Fetching view context for: {downstream_table_name}")
    downstream = fetch_table_metadata(db_client, downstream_table_name)

    upstream_tables = []
    if downstream.view_dependencies and downstream.view_dependencies.dependencies:
        for dep in downstream.view_dependencies.dependencies:
            if dep.table and dep.table.table_full_name:
                upstream_name = dep.table.table_full_name
                logger.info(f"Found upstream dependency: {upstream_name}")
                upstream_tables.append(fetch_table_metadata(db_client, upstream_name))
    else:
        logger.info(f"No view dependencies found for {downstream_table_name}")

    sql_def = downstream.view_definition or ""
    if not sql_def:
        logger.warning(f"No view definition found for {downstream_table_name}")

    return upstream_tables, sql_def, downstream
