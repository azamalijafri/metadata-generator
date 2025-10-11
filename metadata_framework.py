import os
import requests
import json
from databricks.sdk import WorkspaceClient
from groq import Groq
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class MetadataFramework:
    """
    Generates table descriptions and PR metadata by invoking either Databricks
    Foundation Model endpoints or the Groq API, based on configuration.
    """

    def __init__(
        self,
        host: str,
        databricks_token: str,
        llm_provider: str = "databricks",
        model_serving_token: str = None,
        model_endpoint: str = None,
        groq_api_key: str = None,
        groq_model: str = "llama3-8b-8192"
    ):
        """
        Initialize the MetadataFramework.

        Args:
            host: Databricks workspace URL.
            databricks_token: Token for Databricks REST API.
            llm_provider: "databricks" or "groq".
            model_serving_token: Bearer token for Databricks model endpoint.
            model_endpoint: URL of the Databricks model serving endpoint.
            groq_api_key: API key for Groq.
            groq_model: Groq model identifier.
        """
        logger.info("Connecting to Databricks workspace")
        self.db_client = WorkspaceClient(host=host, token=databricks_token)
        self.llm_provider = llm_provider.lower()
        self.model_endpoint = model_endpoint
        self.model_serving_token = model_serving_token
        self.groq_api_key = groq_api_key
        self.groq_model = groq_model
        self.groq_client = None

        if self.llm_provider == "groq":
            if not self.groq_api_key:
                raise ValueError("GROQ_API_KEY is required when using Groq provider")
            self.groq_client = Groq(api_key=self.groq_api_key)
            logger.info(f"Initialized Groq client with model: {self.groq_model}")
        else:
            if not (self.model_endpoint and self.model_serving_token):
                logger.warning("Databricks model endpoint or token not provided")
            else:
                logger.info("Initialized Databricks model serving client")

    def fetch_table_metadata(self, table_name: str):
        """
        Retrieve table metadata from Databricks Catalog.

        Args:
            table_name: Fully qualified table name (e.g., workspace.default.table).

        Returns:
            Metadata object representing the table.
        """
        logger.info(f"Fetching metadata for table: {table_name}")
        try:
            metadata = self.db_client.tables.get(full_name=table_name)
            logger.info(f"Retrieved metadata for {table_name}")
            return metadata
        except Exception as e:
            logger.error(f"Failed to fetch metadata for {table_name}: {e}")
            raise

    def _call_databricks_llm(self, prompt: str) -> str:
        """
        Invoke the Databricks Foundation Model chat endpoint.

        Args:
            prompt: User prompt for the LLM.

        Returns:
            Raw text content from the LLM response.
        """
        headers = {
            "Authorization": f"Bearer {self.model_serving_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": [
                {"role": "system", "content": "You are a data engineer specializing in metadata descriptions. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.3
        }

        logger.info("Sending request to Databricks LLM")
        response = requests.post(self.model_endpoint, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        for part in result["choices"][0]["message"]["content"]:
            if part.get("type") == "text":
                return part["text"]
        logger.warning("No text content found; returning raw JSON")
        return json.dumps(result)

    def _call_groq_llm(self, prompt: str) -> str:
        """
        Invoke the Groq chat completions API.

        Args:
            prompt: User prompt for the LLM.

        Returns:
            Raw text content from the Groq response.
        """
        logger.info(f"Sending request to Groq API (model: {self.groq_model})")
        response = self.groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a data engineer specializing in metadata descriptions. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            model=self.groq_model,
            max_tokens=500,
            temperature=0.3
        )
        return response.choices[0].message.content

    def generate_description_and_pr_metadata(
        self,
        upstream_tables: list,
        downstream_table,
        sql_query: str
    ) -> dict:
        """
        Generate a JSON structure containing the table description and PR metadata.

        Args:
            upstream_tables: List of table metadata objects for upstream inputs.
            downstream_table: Table metadata object for the downstream table.
            sql_query: SQL transformation string.

        Returns:
            Parsed JSON with "description" and "pr_metadata".
        """
        logger.info(f"Preparing prompt for {self.llm_provider.upper()} LLM")

        def format_table_info(table):
            cols = ", ".join(col.name for col in table.columns)
            return f"Table Name: {table.name}\nColumns: {cols}\nDescription: {table.comment or 'No description'}\n"

        upstream_info = "\n".join(format_table_info(t) for t in upstream_tables)
        downstream_cols = ", ".join(col.name for col in downstream_table.columns)
        
        prompt = (
            "Based on the following upstream tables and SQL transformation, generate a JSON response with:\n"
            '1. "description"\n'
            '2. "pr_metadata" containing branch_name, title, body, commit_message\n\n'
            "UPSTREAM TABLES:\n" + upstream_info +
            "\nSQL TRANSFORMATION:\n" + sql_query +
            "\nDOWNSTREAM TABLE SCHEMA:\n" +
            f"Table Name: {downstream_table.name}\nColumns: {downstream_cols}\n\n"
            "Respond with valid JSON only."
        )

        fallback = {
            "description": "Placeholder description.",
            "pr_metadata": {
                "branch_name": "update-downstream-table-desc",
                "title": "Update downstream table metadata description",
                "body": "This PR updates the downstream table description.",
                "commit_message": "Auto-update downstream table metadata description"
            }
        }

        try:
            if self.llm_provider == "groq":
                if not self.groq_client:
                    logger.warning("Groq client not initialized; using fallback")
                    return fallback
                raw = self._call_groq_llm(prompt)
            else:
                if not (self.model_endpoint and self.model_serving_token):
                    logger.warning("Databricks LLM not configured; using fallback")
                    return fallback
                raw = self._call_databricks_llm(prompt)

            result = json.loads(raw.strip())
            logger.info("Parsed JSON from LLM response")
            return result
        except Exception as e:
            logger.error(f"Error invoking {self.llm_provider.upper()} LLM: {e}")
            return fallback

    def run(self, upstream_table_names: list, downstream_table_name: str, sql_query: str) -> dict:
        """
        Fetch metadata, generate the description and PR metadata, and return the result.

        Args:
            upstream_table_names: List of fully qualified upstream table names.
            downstream_table_name: Fully qualified downstream table name.
            sql_query: SQL transformation string.

        Returns:
            JSON dictionary with description and PR metadata.
        """
        logger.info("Running metadata framework")
        upstream = [self.fetch_table_metadata(n) for n in upstream_table_names]
        downstream = self.fetch_table_metadata(downstream_table_name)
        return self.generate_description_and_pr_metadata(upstream, downstream, sql_query)
