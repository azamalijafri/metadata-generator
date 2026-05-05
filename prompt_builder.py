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


def build_clustered_prompt(views_data: list) -> str:
    all_views_info = ""
    for vd in views_data:
        all_views_info += f"\n{'='*60}\n"
        all_views_info += f"DOWNSTREAM VIEW: {vd['downstream'].full_name}\n"
        all_views_info += f"Current Description: {vd['downstream'].comment or 'No description'}\n"
        all_views_info += f"SQL Definition:\n{vd['sql']}\n"
        all_views_info += f"Upstream Tables:\n"
        for up in vd['upstream']:
            all_views_info += format_table_info(up)
        all_views_info += f"Downstream Schema:\n{format_table_info(vd['downstream'])}\n"

    return (
        "You are given metadata for multiple downstream views. "
        "For EACH view, generate a description based on its upstream tables, SQL transformation, and schema.\n\n"
        "Respond with a JSON object containing:\n"
        '1. "descriptions": a dictionary mapping each downstream view full_name to its generated description string\n'
        '2. "pr_metadata": an object with branch_name, title, body, commit_message for a clustered PR covering all views\n\n'
        "VIEWS METADATA:\n" + all_views_info +
        "\nRespond with valid JSON only."
    )
