# Metadata Generator README

## Overview

This repository contains an automated metadata generation framework that:

- Fetches table metadata from Databricks
- Generates descriptive metadata and pull request metadata using an LLM (Databricks or Groq)
- Updates a JSON file with new table descriptions
- Creates or updates a Git branch and opens a GitHub pull request

## Features

- **LLM Provider Options**: Choose between Databricks model serving or Groq API via `LLM_PROVIDER`
- **JSON Append**: Preserve existing entries append/update new descriptions
- **Automated PR**: Branch creation, commit, merge from `main`, push, and PR creation/lookup
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

In the project root, add a `.env` file with the following keys:

```
# Databricks

DATABRICKS_HOST=https://<your-databricks-instance>
DATABRICKS_TOKEN=<your-databricks-token>
MODEL_SERVING_ENDPOINT=<databricks-serving-endpoint-url>
MODEL_SERVING_TOKEN=<databricks-token>

# Groq

GROQ_API_KEY=<your-groq-api-key>
GROQ_MODEL=<your-model>

# LLM Provider: "databricks" or "groq"

LLM_PROVIDER=databricks

# GitHub

GITHUB_TOKEN=<your-github-pat>
REPO_DIR=/path/to/local/repo
REPO_NAME=<github-username/repo-name>
```

### 4. Prepare SQL Files

Place your SQL transformation files in the `sql/` folder. File names should match the downstream table’s simple name.
Example: For `workspace.default.customer_summary`, create `sql/customer_summary.sql`.

### 5. Run the Automation

```
python main.py
```

This will:

1. Load the SQL file
2. Fetch metadata from Databricks
3. Call the LLM to generate description and PR metadata
4. Append/update `table_metadata.json`
5. Create or update a Git branch and open/update a GitHub PR

---

## Folder Structure

```

├── configs/
│ └── table_metadata.json # JSON file with table descriptions
├── sql/ # SQL files for each downstream table
│ └── customer_summary.sql
├── metadata_framework.py # Core logic for metadata and LLM calls
├── github_automation.py # Git + GitHub automation
├── main.py # Entry-point script
├── requirements.txt
└── README.md

```

## License

MIT License.
Feel free to adapt or extend this framework to fit your organization’s metadata workflows.
