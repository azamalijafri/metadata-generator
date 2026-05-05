import json
import logging

logger = logging.getLogger(__name__)


def update_descriptions_in_json(descriptions: dict, current_content: str) -> str:
    logger.info("Updating descriptions in JSON content")
    data = json.loads(current_content) if current_content.strip() else []

    for full_name, description in descriptions.items():
        parts = full_name.split('.')
        schema = parts[1] if len(parts) >= 2 else "default"
        table = parts[2] if len(parts) >= 3 else parts[-1]
        new_entry = {"schema": schema, "table": table, "description": description}

        for i, entry in enumerate(data):
            if entry.get("schema") == schema and entry.get("table") == table:
                data[i] = new_entry
                logger.info(f"Updated existing entry for {schema}.{table}")
                break
        else:
            data.append(new_entry)
            logger.info(f"Added new entry for {schema}.{table}")

    return json.dumps(data, indent=2)
