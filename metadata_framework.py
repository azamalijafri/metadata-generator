import json
import logging
from databricks_client import create_workspace_client
from databricks_metadata import fetch_view_context
from llm_provider import create_llm_client, generate_response
from prompt_builder import build_clustered_prompt

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MetadataFramework:

    def __init__(
        self,
        host: str,
        databricks_token: str,
        llm_provider: str = "databricks",
        model_serving_token: str = None,
        model_serving_endpoint_name: str = None,
        groq_api_key: str = None,
        groq_model: str = "llama3-8b-8192"
    ):
        self.db_client = create_workspace_client(host, databricks_token)
        self.llm_provider = llm_provider.lower()

        if self.llm_provider == "groq":
            self.model_name = groq_model
            api_key = groq_api_key
            if not api_key:
                raise ValueError("GROQ_API_KEY is required when using Groq provider")
            self.llm_client = create_llm_client(
                provider="groq",
                api_key=api_key,
                model=self.model_name
            )
        else:
            self.model_name = model_serving_endpoint_name
            api_key = model_serving_token
            if not api_key:
                raise ValueError("MODEL_SERVING_TOKEN is required when using Databricks provider")
            if not model_serving_endpoint_name:
                raise ValueError("MODEL_SERVING_ENDPOINT_NAME is required when using Databricks provider")

            base_url = host.rstrip("/") + f"/serving-endpoints/{model_serving_endpoint_name}/v1"
            self.llm_client = create_llm_client(
                provider="databricks",
                api_key=api_key,
                model=self.model_name,
                base_url=base_url
            )

    def _collect_view_data(self, downstream_table_names: list) -> list:
        views_data = []
        for table_name in downstream_table_names:
            logger.info(f"Processing view: {table_name}")
            upstream, sql, downstream = fetch_view_context(self.db_client, table_name)
            views_data.append({
                "upstream": upstream,
                "downstream": downstream,
                "sql": sql
            })
        return views_data

    def _generate_clustered_metadata(self, views_data: list) -> dict:
        prompt = build_clustered_prompt(views_data)
        logger.info(f"Preparing prompt for LLM with {len(views_data)} views")

        raw = generate_response(self.llm_client, self.model_name, prompt)
        logger.info(f"Raw LLM response (first 500 chars):\n{raw[:500]}")

        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        result = json.loads(text)
        logger.info("Parsed JSON from LLM response")
        return result

    def run(self, downstream_table_names: list) -> dict:
        logger.info(f"Running metadata framework for {len(downstream_table_names)} views")
        views_data = self._collect_view_data(downstream_table_names)
        return self._generate_clustered_metadata(views_data)
