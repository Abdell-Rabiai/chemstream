"""
ChemStream Producer

Reads sensor data from a CSV file row-by-row and publishes each row as a
JSON message to a Kafka topic. Simulates a real-time IoT sensor feed from
a chemical plant.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable


# ---------- Load configuration ----------
# Look for .env in the project root (one level up from producer/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# When running on host (your laptop), use localhost:9092
# When running inside Docker, use kafka:29092
# We default to the host setting since we'll start by running locally.
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BROKER_HOST_LOCAL", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "tep-sensors")

# Path to CSV: when running on host, use the actual file path.
CSV_PATH = PROJECT_ROOT / "data" / "run1_normal.csv"

# Delay between messages in seconds (0.1 = 100ms)
DELAY_SECONDS = float(os.getenv("PRODUCER_DELAY_MS", "100")) / 1000.0


# ---------- Build the producer ----------
def build_producer() -> KafkaProducer:
    """
    Construct a KafkaProducer with sensible defaults for our use case.

    - bootstrap_servers: where to find the broker
    - value_serializer: how to convert Python objects to bytes
    - acks='all': wait for full broker acknowledgment (durable)
    - retries: auto-retry on transient failures
    - linger_ms: how long to wait to batch messages before sending
    """
    print(f"[producer] connecting to Kafka at {KAFKA_BOOTSTRAP}...")
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BOOTSTRAP],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",
            retries=5,
            linger_ms=10,
        )
        print(f"[producer] connected. Target topic: {KAFKA_TOPIC}")
        return producer
    except NoBrokersAvailable:
        print(
            f"[producer] ERROR: cannot reach Kafka at {KAFKA_BOOTSTRAP}. "
            "Is `docker compose up -d` running?",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------- Stream the CSV ----------
def stream_csv_to_kafka(producer: KafkaProducer) -> None:
    """
    Read the CSV file and publish each row as a JSON message to Kafka.
    Adds an event_time field (when we sent the message) for downstream use.
    """
    if not CSV_PATH.exists():
        print(f"[producer] ERROR: CSV not found at {CSV_PATH}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)
    total = len(df)
    print(f"[producer] loaded {total} rows from {CSV_PATH.name}")
    print(f"[producer] streaming with {DELAY_SECONDS * 1000:.0f}ms delay between messages")
    print("-" * 60)

    sent = 0
    failed = 0

    for idx, row in df.iterrows():
        # Convert the row (a pandas Series) to a plain dict.
        # All values are floats/ints, which json.dumps can serialize natively.
        message = row.to_dict()

        # Add metadata that didn't come from the CSV
        message["event_time"] = datetime.now(timezone.utc).isoformat()

        # Send the message. This is non-blocking; it returns a Future.
        future = producer.send(KAFKA_TOPIC, value=message)

        try:
            # Block for up to 10s waiting for acknowledgment from the broker.
            # In production you'd handle this asynchronously to maximize throughput,
            # but for our 100ms-cadence simulation, a synchronous wait is fine
            # and gives us instant feedback if something is wrong.
            metadata = future.get(timeout=10)
            sent += 1
            if sent % 50 == 0 or sent == 1:
                print(
                    f"[producer] sent {sent}/{total} "
                    f"(partition={metadata.partition}, offset={metadata.offset}, "
                    f"sample={int(message['sample'])}, fault={int(message['faultNumber'])})"
                )
        except KafkaError as e:
            failed += 1
            print(f"[producer] failed to send row {idx}: {e}", file=sys.stderr)

        time.sleep(DELAY_SECONDS)

    # Make sure all buffered messages are flushed before we exit
    producer.flush()
    print("-" * 60)
    print(f"[producer] done. sent={sent}, failed={failed}")


def main() -> None:
    producer = build_producer()
    try:
        stream_csv_to_kafka(producer)
    except KeyboardInterrupt:
        print("\n[producer] interrupted by user")
    finally:
        producer.close()


if __name__ == "__main__":
    main()