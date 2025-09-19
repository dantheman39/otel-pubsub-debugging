# Debugging Open Telemetry's googlecloudpubsubreceiver

I've been experiencing an issue where logs over 4MB are being split in our
observability stack. In trying to understand the issue, I made this
docker compose setup. It has config for:

- A google pubsub emulator.
- A simple Python program that creates a topic and subscription.
  - It also has a command that publishes an 8MB JSON log to the topic.
- An opentelemetry image and config that uses the [googlecloudpubsubreceiver](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/receiver/googlecloudpubsubreceiver)
  to read from the emulator. It outputs to the `debug` exporter,
  meaning you'll see the message in logs. Optionally you can also
  export to an observability platform like SigNoz.

## How to run

You need docker compose. Just run build and run:

```
# Build and run in the background
docker compose up --build -d

# View logs. Run `dk logs -f otel` for only otel logs.
docker compose logs -f

# Once that's all up (see below for how to tell),
# you can publish a large JSON log to the topic by running this:
docker compose run --rm client publish
```

### What you should see

The `pubsub` emulator should be up and running. `docker compose logs pubsub`
should contain this log:

```
pubsub-1  | [pubsub] INFO: Server started, listening on 8085
```

The Python `client` should have created a topic and a subscription, and exited
cleanly. `docker compose logs client`:

```
client-1  | 2025-09-18 21:02:19 [info     ] creating topic                 topic=projects/fake-project/topics/my-topic
client-1  | 2025-09-18 21:02:19 [info     ] creating subscription          subscription=projects/fake-project/subscriptions/my-subscription
```

The `otel` collector should be running. Running `docker compose logs otel`,
before publishing the message there should be a log saying
`Everything is ready. Begin running and processing data.`

Lastly, after you run `docker compose run --rm client publish`, 
you should see two big JSON logs printed to the `otel` logs
(but I wish it were one big message).

The problem is that this is one single large JSON log, but it's apparently being split into
multiple messages when it gets over 4MB. This behavior wasn't happening with
otel 131, before the `googlecloudpubsubreceiver` removed the `raw_text` encoding
in [this PR](https://github.com/open-telemetry/opentelemetry-collector-contrib/pull/41813).

### Optional: send logs to SigNoz

If you have a SigNoz account, uncomment the sections in config.yaml
that set up the otlp exporter and add it to the pipeline.
Before running, run `export SIGNOZ_INGESTION_KEY=<your_key>`
to authenticate. You can run `docker compose down` then `docker compose up -d`
again to restart.
