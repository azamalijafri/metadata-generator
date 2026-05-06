def format_table_info(table) -> str:
    cols = ", ".join(f"{col.name} ({col.type_text or 'unknown'})" for col in table.columns)
    col_details = "\n".join(
        f"  - {col.name}: {col.type_text or 'unknown'} - {col.comment or 'No description'}"
        for col in table.columns
    )
    return (
        f"Table Name: {table.full_name}\n"
        f"Columns: {cols}\n"
        f"Column Details:\n{col_details}\n"
        f"Description: {table.comment or 'No description'}\n"
    )


def format_sample_data(rows: list) -> str:
    if not rows:
        return "  No sample data available.\n"
    lines = []
    for i, row in enumerate(rows):
        values = ", ".join(f"{k}={v}" for k, v in row.items())
        lines.append(f"  Row {i+1}: {{{values}}}")
    return "\n".join(lines) + "\n"


def build_view_prompt(upstream_tables: list, downstream, sql: str, upstream_samples: list, downstream_sample: list) -> str:
    info = ""
    info += f"VIEW: {downstream.full_name}\n"
    info += f"Current Description: {downstream.comment or 'No description'}\n"
    info += f"SQL Definition:\n{sql}\n"
    info += f"Upstream Tables:\n"
    for i, up in enumerate(upstream_tables):
        info += format_table_info(up)
        info += f"Sample Data:\n{format_sample_data(upstream_samples[i])}\n"
    info += f"Downstream Schema:\n{format_table_info(downstream)}\n"
    info += f"Downstream Sample Data:\n{format_sample_data(downstream_sample)}\n"

    return (
        "Generate a concise business-focused description for the view described below.\n\n"
        "Guidelines:\n"
        "- Focus on the business purpose and what the view represents\n"
        "- Describe the transformation logic in plain English\n"
        "- Keep the description around 200 characters\n"
        "- Avoid mentioning column names, table names, or SQL keywords unless necessary\n\n"
        "Respond with valid JSON only in this format:\n"
        '{"description": "Your description here"}\n\n'
        "METADATA:\n" + info +
        "\nRespond with valid JSON only."
    )
