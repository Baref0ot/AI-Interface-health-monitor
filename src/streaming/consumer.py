import json
from confluent_kafka import Consumer
from src.storage.db import get_connection, get_past_events_globally, get_recent_events_for_agency, save_analysis
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
        print(f" Current anomaly: {event['anomaly']}")

        #generate embedding for the event (not currently stored, but could be used for future analysis)
        embedding = generate_embedding(event) 
        print(f"Embedding generated (length: {len(embedding)})")

        ###fetch past events with embeddings to compare against for cross-agency similarity in case we've seen this type of failure before in another agency.
        ##cur.execute("""
        ##    SELECT interface_id, vendor, rows_synced, null_rate, execution_time_ms, anomaly, embedding
        ##    FROM interface_events
        ##    WHERE embedding IS NOT NULL and anomaly IS NOT NULL
        ##    LIMIT 50
        ##""")     
        ##global_agency_events_rows = cur.fetchall()

        ###also fetch the most recent events for this specific interface to potentially infer a root cause from events leading up to this failure.
        ##cur.execute("""
        ##    SELECT interface_id, anomaly, timestamp
        ##    FROM interface_events
        ##    WHERE interface_id = %s
        ##    ORDER BY timestamp DESC
        ##    LIMIT 10
        ##""", (event['interface_id'],))
        ##same_agency_events_rows = cur.fetchall()

        ##global_agency_events = [
        ##    {
        ##        "interface_id": row[0],
        ##        "vendor": row[1],
        ##        "rows_synced": row[2],
        ##        "null_rate": row[3],
        ##        "execution_time_ms": row[4],
        ##        "anomaly": row[5],
        ##        "embedding": row[6],
        ##    }
        ##    for row in global_agency_events_rows
        ##]

        ##same_agency_events = [
        ##{
        ##    "interface_id": row[0],
        ##    "anomaly": row[1],
        ##    "timestamp": row[2],
        ## }
        ## for row in same_agency_events_rows
        ##]

        global_agency_events = get_past_events_globally()
        same_agency_events = get_recent_events_for_agency(event['interface_id'])


        if global_agency_events:
            match, score = find_most_similar(embedding, global_agency_events)

            if same_agency_events:
                print(f"\nRecent events for same agency interface:")
                for e in same_agency_events[:3]:  # limit to avoid spam
                    print(f"  - anomaly={e['anomaly']} timestamp={e['timestamp']}")


            print(f"\nMost similar event from other agencies:")
            print(f" Interface: {match['interface_id']}")
            print(f" Anomaly: {match['anomaly']}")
            print(f" Similarity score: {score:.4f}")

            if not event['anomaly']:
                print("No anomaly detected - skipping root cause analysis.")
                continue

            if score > 0.9:
                print("\nGenerating root cause analysis...\n")

                # call the LLM to generate a root cause analysis based on the current event, the most similar past event from any agency, and the recent history of events for this same agency.
                explanation = generate_root_cause(event, match, score, same_agency_events)

                print(f"Root Cause Analysis:")
                print(explanation)

                # convert the LLM explation to JSON to store in database.
                root_cause_payload = json.dumps(explanation)

                #save the analysis to the database for future reference and learning.
                save_analysis(
                    interface_id=event.get("interface_id"),
                    anomaly=event.get("anomaly"),
                    similarity_score=score,
                    similar_interface_id=match.get("interface_id"),
                    root_cause=root_cause_payload
                )
                print(f"Root cause analysis saved to database.")

            else:
                print("\nNo sufficiently similar past event found for root cause analysis.")

        # create the embedding list of the incoming event to store in postgres along side the event data.
        embedding_list = embedding.tolist() #convert numpy (numpy = the type returned by sentence-transformers) array to list since postgres can store lists but not numpy arrays.


        # Extract fields from event with defaults for missing values.
        interface_id = event['interface_id']  # required
        anomaly = event['anomaly']            # required
        vendor = event.get('vendor', 'unknown')
        timestamp = event.get('timestamp')
        schema_hash = event.get('schema_hash')
        rows_synced = event.get('rows_synced', 0)
        null_rate = event.get('null_rate', 0.0)
        execution_time_ms = event.get('execution_time_ms', 0)

        cur.execute("""
            INSERT INTO interface_events (
                interface_id, vendor, timestamp, 
                rows_synced, null_rate, execution_time_ms, 
                schema_hash, anomaly, embedding
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            interface_id,    
            vendor,    
            timestamp,    
            rows_synced,    
            null_rate,    
            execution_time_ms,    
            schema_hash,    
            anomaly,    
            embedding_list
    ))

        conn.commit() #commit the transaction to save the data. Later we can optimze this by batching commits instead of using one commit per message.

        print(f"Stored event for {event['interface_id']}\n\n")    
    
        
if __name__ == "__main__":
    run_consumer()
        