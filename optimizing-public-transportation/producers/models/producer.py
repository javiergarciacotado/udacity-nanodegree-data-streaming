"""Producer base-class providing common utilites and functionality"""
import logging
import time

from confluent_kafka import avro
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.avro import AvroProducer

logger = logging.getLogger(__name__)

SCHEMA_REGISTRY = "http://localhost:8081"
BOOTSTRAP_SERVER = "PLAINTEXT://localhost:9092"


class Producer:
    """Defines and provides common functionality amongst Producers"""
    # Tracks existing topics across all Producer instances
    existing_topics = set([])

    def __init__(
            self,
            topic_name,
            key_schema,
            value_schema=None,
            num_partitions=1,
            num_replicas=1,
    ):
        """Initializes a Producer object with basic settings"""
        self.topic_name = topic_name
        self.key_schema = key_schema
        self.value_schema = value_schema
        self.num_partitions = num_partitions
        self.num_replicas = num_replicas

        self.broker_properties = {
            "schema.registry.url": SCHEMA_REGISTRY,
            "bootstrap.servers": BOOTSTRAP_SERVER
        }

        # If the topic does not already exist, try to create it
        if self.topic_name not in Producer.existing_topics:
            self.create_topic()
            Producer.existing_topics.add(self.topic_name)

        self.producer = AvroProducer(
            {
                "bootstrap.servers": BOOTSTRAP_SERVER,
                "schema.registry.url": SCHEMA_REGISTRY,
            },
            default_key_schema=key_schema,
            default_value_schema=value_schema
        )

    def create_topic(self):
        """Creates the producer topic if it does not already exist"""
        admin_client = AdminClient({
            "bootstrap.servers": BOOTSTRAP_SERVER
        })

        if not self.exist_topic(admin_client):

            create_topic = admin_client.create_topics([
                NewTopic(
                    topic=self.topic_name,
                    num_partitions=self.num_partitions,
                    replication_factor=self.num_replicas,
                    config={
                        "cleanup.policy": "delete",
                        "compression.type": "lz4",
                        "delete.retention.ms": "100",
                        "file.delete.delay.ms": "100",
                    },
                )
            ])

            for topic, future in create_topic.items():
                try:
                    future.result()
                    logger.info(f"Confirmed topic {topic} creation")
                except Exception as e:
                    logger.error(f"failed to create topic {topic}: {e}")

    def exist_topic(self, admin_client):
        topics_meta = admin_client.list_topics()

        if self.topic_name in topics_meta.topics:
            logger.info(f"Topic {self.topic_name} exists")
            return True

        return False

    def time_millis(self):
        return int(round(time.time() * 1000))

    def close(self):
        """Prepares the producer for exit by cleaning up the producer"""
        logger.info("[close {init}]")
        self.producer.close()

    def time_millis(self):
        """Use this function to get the key for Kafka Events"""
        return int(round(time.time() * 1000))
