from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are a data engineer specializing in metadata descriptions. Always respond with valid JSON."


def create_llm_client(
    provider: str,
    api_key: str,
    model: str,
    base_url: str = None
) -> OpenAI:
    provider = provider.lower()
    if provider == "groq":
        base_url = "https://api.groq.com/openai/v1"
        logger.info(f"Initialized Groq OpenAI client with model: {model}")
    else:
        logger.info(f"Initialized Databricks OpenAI client with base_url: {base_url}")

    return OpenAI(api_key=api_key, base_url=base_url)


def generate_response(client: OpenAI, model: str, prompt: str) -> str:
    logger.info(f"Sending request to LLM (model: {model})")
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        model=model,
        max_tokens=500,
        temperature=0.3
    )
    return response.choices[0].message.content
