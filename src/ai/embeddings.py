from sentence_transformers import SentenceTransformer

#Load model once (singleton) (important!)
model = SentenceTransformer('all-MiniLM-L6-v2')

def event_to_text(event: dict) -> str:
    """
    Convert structured event into human-readable text for embedding.
    """
    return (
        f"Interface {event['interface_id']} from {event['vendor']} "
        f"Processed {event['rows_synced']} rows, "
        f"null rate {event['null_rate']}, "
        f"execution time {event['execution_time_ms']} ms, "
        f"schema hash {event['schema_hash']}, "
        f"anomaly type {event['anomaly']}"
    )

def generate_embedding(event: dict):
    """
    Generate embedding for a given event.
    """
    text = event_to_text(event)
    embedding = model.encode(text)
    return embedding

