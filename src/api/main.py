from fastapi import FastAPI
from typing import List
from src.models.models import InterfaceEvent
from src.generator.synthetic import generate_batch
import logging

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
def get_events():
    return EVENT_STORE


@app.get("/alerts")
def get_alerts():
    # For Phase 1, alerts = events with anomalies
    return [event for event in EVENT_STORE if event.anomaly]