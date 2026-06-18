from sentence_transformers import SentenceTransformer

#Load model once (singleton) (important!)
model = SentenceTransformer('all-MiniLM-L6-v2')

def event_to_text(event):
    return f"""
        Interface: {event.get('interface_id')}
        Type: {event.get('interface_type')}
        Vendor: {event.get('vendor')}
    
        Exception Type: {event.get('exception_type')}
        Module: {event.get('module')}
    
        Error Message:
        {event.get('error_message')}
    
        Fingerprint:
        {event.get('fingerprint')}
    """

def generate_embedding(event: dict):
    """
    Generate embedding for a given event.
    """
    text = event_to_text(event)
    embedding = model.encode(text)
    return embedding

