from pydantic import BaseModel # For data validation + serialization (import for FastAPI and Kafka later)
from typing import Optional    # For optional fields (like anomaly detection results)
from datetime import datetime  # For timestamping events


# model used for consistent data representation across the system (Kafka, FastAPI, etc.)
class InterfaceEvent (BaseModel):
    interface_id: str
    vendor: str
    timestamp: datetime
    rows_synced: int
    null_rate: float
    execution_time_ms: int
    schema_hash: str
    anomaly: Optional[str] = None