# Metadata Generator README

## Overview

This repository contains an automated metadata generation framework that:

- Accepts a list of downstream view names
- Fetches upstream lineage and SQL definitions directly from Databricks Unity Catalog
- Generates descriptions for all views using an LLM (Databricks or Groq)
- Creates a single clustered PR updating `configs/table_metadata.json` with all descriptions

## Features

- **LLM Provider Options**: Choose between Databricks model serving or Groq API via `LLM_PROVIDER`
- **OpenAI-compatible**: Uses the `openai` SDK for both providers — just pass the appropriate API key
- **Automatic Lineage**: Upstream dependencies are resolved from Databricks `view_dependencies`
- **SQL from Databricks**: View SQL definitions are fetched via `view_definition` from the catalog
- **Clustered PR**: All views are processed together in one branch/PR
- **JSON Append**: Preserve existing entries, append/update new descriptions
- **Server-side Git**: All Git operations happen via the GitHub API (no local repo needed)
- **Config via .env**: All credentials and settings are loaded from environment variables

---

## Getting Started

### 1. Clone the Repository

```
git clone https://github.com/azamalijafri/metadata-generator.git
cd metadata-generator
```

### 2. Install Dependencies

```
pip install -r requirements.txt
```

### 3. Create `.env` File

Copy `.env.sample` and fill in your values:

```
cp .env.sample .env
```

### 4. Configure Views

Edit the `downstream_views` list in `main.py` with your target views:

```python
downstream_views = [
    "workspace.default.customer_summary",
    "workspace.default.order_summary"
]
```

### 5. Run the Automation

```
python main.py
```

This will:

1. For each downstream view, fetch upstream lineage and SQL definition from Databricks
2. Call the LLM to generate descriptions and clustered PR metadata
3. Update `table_metadata.json` with all descriptions
4. Create a Git branch via GitHub API, commit, and open a PR

---

## File Structure

```
├── configs/
│   └── table_metadata.json       # JSON file with table descriptions
├── databricks_client.py          # Databricks WorkspaceClient creation
├── databricks_metadata.py        # Table metadata, lineage, SQL fetching
├── llm_provider.py               # OpenAI client factory (Databricks + Groq)
├── prompt_builder.py             # Table formatting + prompt building
├── github_ops.py                 # File CRUD + branch creation via GitHub API
├── github_pr.py                  # PR creation and lookup
├── github_metadata.py            # JSON description updates
├── github_automation.py          # PR orchestration (public entry point)
├── metadata_framework.py         # Orchestrates databricks + llm
├── main.py                       # Entry-point script
├── requirements.txt
├── .env.sample                   # Template for environment variables
└── README.md
```

## License

MIT License.
Feel free to adapt or extend this framework to fit your organization's metadata workflows.
