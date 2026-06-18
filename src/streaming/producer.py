import json
import time
from confluent_kafka import Producer
from src.generator.synthetic import generate_event


print("Producer file loaded")

KAFKA_BROKER = "localhost:9092"
TOPIC = "interface-events"

def create_producer():
    return Producer({
        "bootstrap.servers": KAFKA_BROKER
    })

def run_producer():
    producer = create_producer()

    print("Producer started... \n")

    while True:
        event = generate_event()

        producer.produce(
            topic=TOPIC,
            key=event.interface_id,
            value=event.model_dump_json(),
        )

        producer.flush() # Ensure the message is sent before proceeding
        print(f"Sent event for {event.interface_id}")

        time.sleep(2) # Sleep for 2 seconds before sending the next event

if __name__ == "__main__":
    run_producer()



def produce_event(event_dict: dict):
    producer = create_producer()

    producer.produce(
        topic=TOPIC,
        key=event_dict.get("interface_id", "unknown"),
        value=json.dumps(event_dict),
    )

    producer.flush()
    print(f" Sent ingested event for {event_dict.get('interface_id')}")