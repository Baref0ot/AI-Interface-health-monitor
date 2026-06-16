from dotenv import load_dotenv #used to load environment variables from .env file.
import os
from openai import OpenAI

load_dotenv() # loads .env into environment

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_root_cause(current_event: dict, similar_event: dict, similarity_score: float) -> str:
    """
    Use OpenAI to generate a root cause analysis based on the current event and a similar past event.
    """
    prompt = f"""
        You are an expert in diagnosing data interface issues.

        STRICT RULES:
        - Only use the data provided below.
        - Do NOT mention any vendor, system, or technology that is not explicitly listed.
        - If unsure, say "insufficient information" instead of guessing.

        CURRENT EVENT:
        Interface: {current_event['interface_id']}
        Vendor: {current_event['vendor']}
        Rows Synced: {current_event['rows_synced']}
        Null Rate: {current_event['null_rate']}
        Execution Time: {current_event['execution_time_ms']}
        Anomaly: {current_event['anomaly']}

        SIMILAR PAST EVENT:
        Interface: {similar_event['interface_id']}
        Vendor: {similar_event['vendor']}
        Rows Synced: {similar_event['rows_synced']}
        Null Rate: {similar_event['null_rate']}
        Execution Time: {similar_event['execution_time_ms']}
        Anomaly: {similar_event['anomaly']}

        Similarity Score: {similarity_score:.2f}

        Explain the most likely root cause based ONLY on this data.
        Be concise (2–3 sentences).
        Do not introduce external assumptions.
    """ 

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3, # Lower temperature for more deterministic output since we want consistent root cause analysis 
    )

    return response.choices[0].message.content