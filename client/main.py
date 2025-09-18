from google.api_core.exceptions import NotFound
from google.cloud import pubsub_v1
import os
import structlog
import sys


def create_topic_if_not_exists(publisher: pubsub_v1.PublisherClient, name: str) -> None:
    logger = structlog.get_logger()
    try:
        publisher.get_topic(topic=name)
        logger.info("topic already exists", topic=name)
        return

    except NotFound:
        pass

    logger.info("creating topic", topic=name)
    publisher.create_topic(name=name)


def create_subscription_if_not_exists(subscriber: pubsub_v1.SubscriberClient, topic_name: str, subscription_name: str) -> None:
    logger = structlog.get_logger()
    try:
        subscriber.get_subscription(subscription=subscription_name)
        logger.info("subscription already exists", subscription=subscription_name)
        return

    except NotFound:
        pass

    logger.info("creating subscription", subscription=subscription_name)
    subscriber.create_subscription(topic=topic_name, name=subscription_name)


def publish_json_file(publisher: pubsub_v1.PublisherClient, topic_name: str, file_path: str):
    with open(file_path, "rb") as fh:
        data = fh.read()
        future = publisher.publish(topic=topic_name, data=data)
        future.result()


if __name__ == "__main__":
    logger = structlog.get_logger()

    project_id = os.environ.get("PUBSUB_PROJECT_ID")
    topic = os.environ.get("PUBSUB_TOPIC")
    subscription = os.environ.get("PUBSUB_SUBSCRIPTION")

    for v in (("PUBSUB_PROJECT_ID", project_id), ("PUBSUB_TOPIC", topic), ("PUBSUB_SUBSCRIPTION", subscription)):
        if v[1] is None:
            logger.error(f"missing required environment variable: {v[0]}")
            sys.exit(1)

    topic_name = f"projects/{project_id}/topics/{topic}"
    subscription_name = f"projects/{project_id}/subscriptions/{subscription}"

    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()

    if len(sys.argv) > 1 and sys.argv[1] == "publish":
        logger.info("publishing message")
        with publisher:
            publish_json_file(publisher=publisher, topic_name=topic_name, file_path="./big_log.json")
        sys.exit(0)

    with publisher:
        with subscriber:
            create_topic_if_not_exists(publisher, topic_name)
            create_subscription_if_not_exists(subscriber, topic_name, subscription_name)
