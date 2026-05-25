import json
import os

from stream.sentiment_processor import SentimentProcessor


def consume_once(topic: str = "earnings-raw") -> list[dict]:
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    try:
        from confluent_kafka import Consumer
        consumer = Consumer({"bootstrap.servers": bootstrap, "group.id": "earningsiq-nlp", "auto.offset.reset": "earliest"})
        consumer.subscribe([topic])
        message = consumer.poll(5)
        consumer.close()
        if message and not message.error():
            payload = json.loads(message.value().decode("utf-8"))
            return [payload]
    except Exception:
        return []
    return []


def process_messages(messages: list[dict]) -> list[dict]:
    processor = SentimentProcessor()
    output: list[dict] = []
    for message in messages:
        analysis = processor.analyze([message.get("sentence_text", "")])
        output.append({**message, **analysis})
    return output
