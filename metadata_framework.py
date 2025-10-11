import os
import requests
from databricks.sdk import WorkspaceClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetadataFramework:
    def __init__(self, host, databricks_token, model_serving_token=None, model_endpoint=None):
        self.db_client = WorkspaceClient(host=host, token=databricks_token)
        self.model_endpoint = model_endpoint
        self.model_serving_token = model_serving_token

    def fetch_table_metadata(self, table_name):
        return self.db_client.tables.get(full_name=table_name)

    def generate_description(self, upstream_tables, downstream_table, sql_query):
        def format_table_info(table):
            columns = ', '.join(col.name for col in table.columns)
            return (
                f"Table Name   : {table.name}\n"
                f"Description  : {table.comment or 'No description'}\n"
                f"Columns      : {columns}\n"
            )

        upstream_info = "\n".join(format_table_info(table) for table in upstream_tables)
        downstream_cols = ', '.join(col.name for col in downstream_table.columns)

        logger.info("Upstream Tables Info:\n%s", upstream_info)
        logger.info("Downstream Table Info:\n%s", downstream_cols)

        prompt = (
            "Based on the following upstream tables and SQL transformation, generate a clear and informative description for the downstream table.\n\n"
            "UPSTREAM TABLES:\n"
            f"{upstream_info}\n"
            "SQL TRANSFORMATION:\n"
            f"{sql_query}\n"
            "DOWNSTREAM TABLE SCHEMA:\n"
            f"Table Name   : {downstream_table.name}\n"
            f"Columns      : {downstream_cols}\n\n"
            "Please generate a concise description (2-3 sentences) that explains:\n"
            "1. What this table contains\n"
            "2. How it's derived from the upstream tables\n"
            "3. Its primary business purpose\n\n"
            "Description:"
        )

        if not self.model_endpoint or not self.model_serving_token:
            logger.warning("Model endpoint or token is not provided, returning placeholder description.")
            return "This is a placeholder description generated for the downstream table based on upstream tables and SQL transformation."

        headers = {
            "Authorization": f"Bearer {self.model_serving_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a data engineer specializing in metadata descriptions."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 400,
            "temperature": 0.3
        }

        try:
            response = requests.post(self.model_endpoint, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            # Extract the description from 'choices[0].message.content' where 'type' == 'text'
            content_parts = result['choices'][0]['message']['content']
            description = ""
            for part in content_parts:
                if part.get('type') == 'text' and 'text' in part:
                    description = part['text']
                    break

            if not description:
                # Fallback: convert whole response to string
                description = str(result)

            return description.strip()
        except Exception as e:
            logger.error("Error during model serving invocation: %s", e)
            return "Failed to generate description due to model invocation error."

    def run(self, upstream_table_names, downstream_table_name, sql_query):
        upstream_tables = [self.fetch_table_metadata(name) for name in upstream_table_names]
        downstream_table = self.fetch_table_metadata(downstream_table_name)
        final_description = self.generate_description(upstream_tables, downstream_table, sql_query)
        return final_description
