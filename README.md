# Context Forge

Automated metadata generation for Databricks views with GitHub PR automation.

## Installation

```bash
pip install context-forge
```

Or from source:

```bash
git clone https://github.com/azamalijafri/context-forge.git
cd context-forge
pip install -e .
```

## Usage

```python
from context_forge import ContextForge, automate_github_pr

# Initialize
cf = ContextForge(
    host="https://your-databricks-instance",
    databricks_token="your-token",
    llm_provider="groq",                    # or "databricks"
    groq_api_key="your-groq-key",
    groq_model="llama3-8b-8192",
    warehouse_http_path="/sql/1.0/warehouses/your-id"
)

# Generate descriptions for downstream views
result = cf.run([
    "workspace.default.customer_summary",
    "workspace.default.order_summary"
])

# Open a GitHub PR with the generated descriptions
pr_url = automate_github_pr(
    descriptions=result["descriptions"],
    branch_name=result["branch_name"],
    commit_msg=result["commit_message"],
    pr_title=result["pr_title"],
    pr_body=result["pr_body"],
    repo_name="your-username/your-repo",
    github_token="your-github-pat"
)
```

## Configuration

### Databricks
| Parameter | Description |
|---|---|
| `host` | Databricks workspace URL |
| `databricks_token` | Databricks personal access token |
| `warehouse_http_path` | SQL warehouse HTTP path (for sample data) |

### LLM
| Provider | Parameters |
|---|---|
| **Groq** | `llm_provider="groq"`, `groq_api_key`, `groq_model` |
| **Databricks** | `llm_provider="databricks"`, `model_serving_token`, `model_serving_endpoint_name` |

### GitHub
| Parameter | Description |
|---|---|
| `repo_name` | GitHub repo in `owner/repo` format |
| `github_token` | PAT with `repo` scope |

## How It Works

1. For each downstream view, fetches upstream lineage from Databricks Unity Catalog
2. Retrieves the view SQL definition and 3 sample rows per table
3. Sends isolated context to the LLM to generate a ~200 char business-focused description
4. Collects all descriptions into a single commit on `configs/table_metadata.json`
5. Opens a clustered GitHub PR

## File Structure

```
├── context_forge/
│   ├── __init__.py               # Public API
│   ├── framework.py              # ContextForge orchestrator
│   ├── databricks_client.py      # WorkspaceClient creation
│   ├── databricks_metadata.py    # Table metadata, lineage, sample data
│   ├── llm_provider.py           # OpenAI client factory
│   ├── prompt_builder.py         # LLM prompt construction
│   ├── github_ops.py             # File + branch operations
│   ├── github_pr.py              # PR creation
│   ├── github_metadata.py        # JSON updates
│   └── github_automation.py      # PR orchestration
├── examples/
│   └── run.py                    # Example script
├── pyproject.toml
├── .env.sample
└── README.md
```

## License

MIT
