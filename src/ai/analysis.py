from dotenv import load_dotenv #used to load environment variables from .env file.
import os
import json
from openai import OpenAI

load_dotenv() # loads .env into environment

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



def generate_root_cause(current_event: dict, similar_event: dict, similarity_score: float, recent_events_of_same_agency: dict) -> dict:
    """
    Use OpenAI to generate a root cause analysis based on the current event and a similar past event.
    """

    formatted_history = [ 
        f"{e['timestamp']} → {e['anomaly']}" 
        for e in recent_events_of_same_agency
    ]

    prompt = f"""
        You are a senior backend engineer supporting police CAD/RMS integrations.

        Your job is to diagnose integration failures and infer likely system configuration or operational issues.

        --- CURRENT EVENT ---
        Interface: {current_event.get("interface_id")}
        Exception Type: {current_event.get("exception_type")}
        Module: {current_event.get("module")}
        Interface Type: {current_event.get("interface_type")}

        Error Message:
        {current_event.get("error_message")}

        --- MOST SIMILAR PAST EVENT (GLOBAL) ---
        Interface: {similar_event.get("interface_id")}
        Anomaly: {similar_event.get("anomaly")}
        Similarity Score: {similarity_score}

        --- RECENT HISTORY (SAME AGENCY / INTERFACE) ---
        Most recent first:
        {formatted_history}

        INSTRUCTIONS:

        1. Explain what the error means in plain English.
        2. Identify the most likely root cause based on the error itself.
        3. Infer what type of system configuration is being used (e.g., API integration, database connection, Windows auth, etc.).
        4. Analyze the recent history carefully and form a CLEAR conclusion:
            - If multiple errors occur at the same timestamp, interpret this as a system-wide or batch failure, NOT isolated incidents
            - Look for time-based patterns such as recurring failures (e.g., weekly/monthly intervals), sudden gaps, or repeated timestamps
            - If events occur at regular intervals (e.g., ~30 days apart), consider causes such as scheduled jobs, certificate/token expiration, or recurring configuration drift
            - If patterns are approximate (e.g., ~30 days apart), describe them as approximate rather than exact
            - Determine whether the pattern suggests:
            - batch processing failure
            - upstream data issue
            - API outage or rejection
            - deployment or configuration change
            - Do not just describe the pattern — EXPLAIN what it likely indicates and why
        5. Combine the error details AND the historical pattern to form a STRONG, specific hypothesis about what failed
            - Avoid vague statements like “could be” or “may be”
            - Prioritize the MOST likely explanation
        6. Suggest the FIRST things an engineer should check before contacting the customer.
        7. Explain why this type of issue commonly occurs in real-world environments.

        IMPORTANT:
        - Be specific and practical, not generic.
        - If the history does NOT suggest a pattern, ignore it.
        - If a pattern IS present, explicitly call it out and use it in your reasoning.
        - Prioritize actionable troubleshooting steps.

        ANSWER FORMAT:

        Root Cause:
        <short summary of the issue>

        What it means:
        <plain English explanation>

        Observed Pattern (if any):
        <what you see from recent_events_of_same_agency>

        Likely System Setup (inferred):
        <what kind of system/config is likely in use>

        Most Likely Cause:
        <your best hypothesis>

        What to Check FIRST:
        <top actionable steps>

        Why This Happens:
        <root explanation of why systems fail this way>

        Return ONLY valid JSON in this exact shape:
        {{  "root_cause": "",  
            "what_it_means": "",  
            "observed_pattern": "",  
            "likely_system_setup": "",  
            "most_likely_cause": "",  
            "what_to_check_first": [],  
            "why_this_happens": ""
        }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3, # Lower temperature for more deterministic output since we want consistent root cause analysis 
    )

    content = response.choices[0].message.content

    try:
       return json.loads(content)
    except json.JSONDecodeError:
        return {
            "error": "LLM did not return valid JSON",
            "root_cause": "Unable to parse structured response",
            "what_it_means": content,
            "observed_pattern": "",
            "likely_system_setup": "",
            "most_likely_cause": "",
            "what_to_check_first": [],
            "why_this_happens": ""
        }