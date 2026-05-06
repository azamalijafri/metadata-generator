import json
import re
import logging
from .databricks_client import create_workspace_client
from .databricks_metadata import fetch_view_context, fetch_sample_rows
from .llm_provider import create_llm_client, generate_response
from .prompt_builder import build_view_prompt

logger = logging.getLogger(__name__)

PR_BRANCH = "update-table-metadata-descriptions"
PR_TITLE = "Update table metadata descriptions"
PR_BODY = "Auto-generated descriptions for downstream views."
COMMIT_MESSAGE = "Auto-update downstream table metadata descriptions"


class ContextForge:

    def __init__(
        self,
        host: str,
        databricks_token: str,
        llm_provider: str = "databricks",
        model_serving_token: str = None,
        model_serving_endpoint_name: str = None,
        groq_api_key: str = None,
        groq_model: str = "llama3-8b-8192",
        warehouse_http_path: str = None
    ):
        self.db_client = create_workspace_client(host, databricks_token)
        self.host = host
        self.token = databricks_token
        self.http_path = warehouse_http_path
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

    def _extract_description(self, raw: str) -> str:
        logger.info(f"Raw LLM response:\n{raw}")

        text = raw.strip()

        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        try:
            result = json.loads(text)
            if "description" in result:
                return result["description"]
        except json.JSONDecodeError:
            pass

        match = re.search(r'"description"\s*:\s*"([^"]*)"', text)
        if match:
            return match.group(1)

        if text and not text.startswith("{"):
            return text

        raise ValueError(f"Could not extract description from LLM response:\n{raw}")

    def _generate_description(self, upstream_tables: list, downstream, sql: str, upstream_samples: list, downstream_sample: list) -> str:
        prompt = build_view_prompt(upstream_tables, downstream, sql, upstream_samples, downstream_sample)
        logger.info(f"Generating description for: {downstream.full_name}")

        raw = generate_response(self.llm_client, self.model_name, prompt)
        return self._extract_description(raw)

    def _fetch_sample(self, table_name: str) -> list:
        if not self.http_path:
            return []
        return fetch_sample_rows(self.host, self.http_path, self.token, table_name)

    def run(self, downstream_table_names: list) -> dict:
        logger.info(f"Running ContextForge for {len(downstream_table_names)} views")

        descriptions = {}
        for table_name in downstream_table_names:
            logger.info(f"Processing view: {table_name}")
            upstream, sql, downstream = fetch_view_context(self.db_client, table_name)

            upstream_samples = []
            for up_table in upstream:
                sample = self._fetch_sample(up_table.full_name)
                upstream_samples.append(sample)

            downstream_sample = self._fetch_sample(downstream.full_name)

            description = self._generate_description(upstream, downstream, sql, upstream_samples, downstream_sample)
            descriptions[table_name] = description
            logger.info(f"Generated Description for {table_name}: {description}")

        return {
            "descriptions": descriptions,
            "branch_name": PR_BRANCH,
            "pr_title": PR_TITLE,
            "pr_body": PR_BODY,
            "commit_message": COMMIT_MESSAGE
        }
