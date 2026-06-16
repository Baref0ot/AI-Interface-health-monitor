import random
import uuid
from datetime import datetime
from typing import List
from src.models.models import InterfaceEvent

INTERFACES = [
      ("arcadia-pd-rms", "CentralSquare"),    
      ("metro-nashville-cad", "Motorola"),    
      ("dallas-pd-rms", "TylerTech"),
]

ANOMALY_TYPES = [
     None,    
     "volume_drop",    
     "null_spike",    
     "slow_query",    
     "schema_change",    
     "total_failure",
]

def generate_normal_event(interface_id: str, vendor: str) -> InterfaceEvent:
    return InterfaceEvent(
       interface_id = interface_id,        
       vendor = vendor,        
       timestamp = datetime.now(),        
       rows_synced = random.randint(1000, 3000),        
       null_rate = round(random.uniform(0.0, 0.05), 4),        
       execution_time_ms = random.randint(800, 2000),        
       schema_hash = str(uuid.uuid4())[:8],        
       anomaly = None,
    ) 


def inject_anomaly(event: InterfaceEvent, anomaly_type: str) -> InterfaceEvent:    
    if anomaly_type == "volume_drop":        
        event.rows_synced = random.randint(0, 200)    
    elif anomaly_type == "null_spike":        
        event.null_rate = round(random.uniform(0.2, 0.6), 4)    
    elif anomaly_type == "slow_query":        
        event.execution_time_ms = random.randint(5000, 15000)    
    elif anomaly_type == "schema_change":        
        event.schema_hash = str(uuid.uuid4())[:8]    
    elif anomaly_type == "total_failure":        
        event.rows_synced = 0        
        event.execution_time_ms = random.randint(20000, 60000)    
        
    event.anomaly = anomaly_type    
    return event





def generate_event(anomaly_probability: float = 0.2) -> InterfaceEvent:
    interface_id, vendor = random.choice(INTERFACES)
    event = generate_normal_event(interface_id, vendor)

    if random.random() < anomaly_probability:
        anomaly = random.choice(ANOMALY_TYPES[1:])  # exclude None
        event = inject_anomaly(event, anomaly)

    return event


def generate_batch(size: int = 10) -> List[InterfaceEvent]:    
    return [generate_event() for _ in range(size)]