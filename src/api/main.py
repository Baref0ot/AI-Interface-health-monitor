from fastapi import FastAPI
from typing import List
from src.models.models import InterfaceEvent
from src.generator.synthetic import generate_batch
import logging
from datetime import datetime
from src.ai.similarity import find_most_similar
from src.ai.embeddings import generate_embedding
from src.ai.analysis import generate_root_cause
from src.storage.db import get_all_events, get_all_events_with_embeddings, get_anomalies, get_latest_event
from src.streaming.producer import produce_event

app = FastAPI(title="Interface Health Monitor")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Temporary in-memory storage
EVENT_STORE: List[InterfaceEvent] = []


@app.get("/")
def root():
    return {"message": "Interface Health Monitor API is running"}


@app.post("/generate")
def generate_events(count: int = 10):
    global EVENT_STORE
    new_events = generate_batch(count)
    EVENT_STORE.extend(new_events)
    logger.info(f"Generated {len(new_events)} events.")
    return {"generated": len(new_events)}


@app.get("/interfaces", response_model=List[InterfaceEvent])
def get_interfaces():
    return get_all_events()


@app.get("/alerts")
def get_alerts():
    return get_anomalies()



@app.post("/analyze")
def analyze(interface_id: str):

    # Step 1: get current event
    current_event = get_latest_event(interface_id)

    if not current_event:
        return {"error": "No event found"}

    # Step 2: embedding
    embedding = generate_embedding(current_event)

    # Step 3: get past events
    past_events = get_all_events_with_embeddings()

    # Step 4: similarity
    match, score = find_most_similar(embedding, past_events)

    # Step 5: gating
    if not current_event.get("anomaly"):
        return {
            "interface_id": interface_id,
            "message": "No anomaly detected"
        }

    # Step 6: LLM
    explanation = generate_root_cause(current_event, match, score)

    return {
        "interface_id": interface_id,
        "current_event": current_event,
        "similar_event": {
            "interface_id": match["interface_id"],
            "anomaly": match["anomaly"]
        },
        "similarity_score": score,
        "root_cause": explanation
    }


@app.post("/ingest/error-log")
def ingest_error_log(payload: dict):
    print("\n -----Incoming error log:-----")
    print(payload)

    event = transform_error_log(payload)

    print("\n ----- Transformed event:-----")
    print(event)

    produce_event(event)

    return {"status": "ingested"}


def transform_error_log(payload: dict):
    tags = payload.get("tags", {})
    exception_block = payload.get("exception", {})
    error_meta = payload.get("error", {})

    # pull exception safely
    exception_values = exception_block.get("values", [{}])
    exception_data = exception_values[0] if exception_values else {}

    error_message = exception_data.get("value", "")
    module = exception_data.get("module", "")
    exception_type = error_meta.get("type", "")

    # extract identifiers
    interface_id = tags.get("APIUser", "unknown")
    interface_type = tags.get("Interface", "unknown")
    vendor = tags.get("app", "unknown")

    fingerprint = payload.get("fingerprint", [])

    timestamp = payload.get("timestamp") or payload.get("date")

    return {
        "interface_id": interface_id,
        "interface_type": interface_type,
        "vendor": vendor,

        # USE REAL TIMESTAMP (not generated)
        "timestamp": timestamp,

        # required fields for your system
        "rows_synced": 0,
        "null_rate": 0.5 if "null" in error_message.lower() else 0.01,
        "execution_time_ms": 1000,

        "anomaly": "error_event",

        # SAFE + USEFUL FIELDS FOR AI
        "exception_type": exception_type,
        "error_message": error_message,
        "module": module,
        "fingerprint": fingerprint
    }
