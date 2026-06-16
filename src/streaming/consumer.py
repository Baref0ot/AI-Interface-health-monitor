import json
from confluent_kafka import Consumer
from src.storage.db import get_connection
from src.ai.embeddings import generate_embedding
from src.ai.similarity import find_most_similar
from src.ai.analysis import generate_root_cause

#where Kafka is running (from your machine's perspective)
KAFKA_BROKER = 'localhost:9092'
TOPIC = 'interface-events'


def create_consumer():
    return Consumer({
        "bootstrap.servers": KAFKA_BROKER,
        "group.id": "interface-health-group",
        "auto.offset.reset": "earliest",  #read from beginning of topic
    })

def run_consumer():
    consumer = create_consumer()
    consumer.subscribe([TOPIC])

    conn = get_connection()
    cur = conn.cursor()

    print(f"listening for events on topic: {TOPIC}... \n")

    while True:
        msg = consumer.poll(1.0) #.poll(1.0) waits for 1 second for a message and returns None if no message is received.

        if msg is None:
            continue #no message received, continue waiting

        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue

        event = json.loads(msg.value().decode('utf-8')) #decode bytes to string and parse JSON
        print(f"\nReceived event for {event['interface_id']}")

        embedding = generate_embedding(event) #generate embedding for the event (not currently stored, but could be used for future analysis)
        print(f"Embedding generated (length: {len(embedding)})")

        cur.execute("""
            SELECT
                interface_id,
                anomaly,
                embedding
            FROM interface_events
            WHERE embedding IS NOT NULL
            LIMIT 50
        """)

        rows = cur.fetchall()

        past_events = [
            {
                "interface_id": row[0],
                "anomaly": row[1],
                "embedding": row[2],
            }
            for row in rows
        ]

        if past_events:
            match, score = find_most_similar(embedding, past_events)

            print(f"\nMost similar event:")
            print(f" Interface: {match['interface_id']}")
            print(f" Anomaly: {match['anomaly']}")
            print(f" Similarity score: {score:.4f}")

            if score > 0.8:
                print("\nGenerating root cause analysis...\n")
                explanation = generate_root_cause(event, match, score)
                print(f"Root Cause Analysis:")
                print(explanation)


        embedding_list = embedding.tolist() #convert numpy (numpy = the type returned by sentence-transformers) array to list since postgres can store lists but not numpy arrays.

        cur.execute("""
            INSERT INTO interface_events (
                interface_id, vendor, timestamp, 
                rows_synced, null_rate, execution_time_ms, 
                schema_hash, anomaly, embedding
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            event['interface_id'],
            event['vendor'],
            event['timestamp'],
            event['rows_synced'],
            event['null_rate'],
            event['execution_time_ms'],
            event['schema_hash'],
            event['anomaly'],
            embedding_list
    ))

        conn.commit() #commit the transaction to save the data. Later we can optimze this by batching commits instead of using one commit per message.

        print(f"Stored event for {event['interface_id']}\n\n")    
    
        
if __name__ == "__main__":
    run_consumer()
        