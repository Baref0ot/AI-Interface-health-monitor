from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_root_cause(current_event: dict, similar_event: dict, similarity_score: float) -> str:
    """
    Use OpenAI to generate a root cause analysis based on the current event and a similar past event.
    """
    prompt = f"""
    You are an expert in diagnosing data interface issues in law enforcement systems
    
    A new event occurred:
    Interface: {current_event['interface_id']}
    Vendor: {current_event['vendor']}
    Rows Synced: {current_event['rows_synced']}
    Null Rate: {current_event['null_rate']}
    Execution Time: {current_event['execution_time_ms']}
    Anomaly: {current_event['anomaly']}

    A similar past event was found:
    Interface: {similar_event['interface_id']}
    Anomaly: {similar_event['anomaly']}

    Similarity score: {similarity_score: .2f}

    Based on this, explain the most likely root cause in plain English.
    Be concise (2-3 sentences) and actionable.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3, # Lower temperature for more deterministic output since we want consistent root cause analysis 
    )

    return response.choices[0].message.content