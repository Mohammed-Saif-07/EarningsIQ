import json
import os


class EarningsProducer:
    def __init__(self, topic: str = "earnings-raw") -> None:
        self.topic = topic
        self.bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self._producer = None
        if os.getenv("USE_KAFKA", "false").lower() not in {"1", "true", "yes"}:
            return
        try:
            from confluent_kafka import Producer
            self._producer = Producer({"bootstrap.servers": self.bootstrap})
        except Exception:
            self._producer = None

    def send(self, key: str, value: dict) -> bool:
        if self._producer is None:
            print(json.dumps({"topic": self.topic, "key": key, "value": value}))
            return False
        self._producer.produce(self.topic, key=key, value=json.dumps(value).encode("utf-8"))
        self._producer.poll(0)
        return True

    def flush(self, timeout: float = 10.0) -> None:
        if self._producer is not None:
            self._producer.flush(timeout)
