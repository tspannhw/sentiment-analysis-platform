# Sentiment Analysis Back-end

## Architecture
- Elasticsearch
- Apache Pulsar
- RestAPI + WebSockets
- Background Tweet 'crawler'

## Summary
Elasticsearch stores tweets processed through pulsar and pulsar-functions.
The crawler is a set of scripts/functions that load/stream data into pulsar and parse/run's NLP Sentiment Analysis.
The API will query Elasticsearch, and trigger crawler jobs to load content into Elasticsearch.

### To run [Pulsar](https://pulsar.apache.org/docs/en/standalone-docker/) locally
```bash
docker run -it \
  -p 6650:6650 \
  -p 8080:8080 \
  --mount source=pulsardata,target=/pulsar/data \
  --mount source=pulsarconf,target=/pulsar/conf \
  apachepulsar/pulsar:2.8.1 \
  bin/pulsar standalone
```

### To run [Elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html) locally
```bash
docker pull docker.elastic.co/elasticsearch/elasticsearch:7.15.2
docker run -p 127.0.0.1:9200:9200 -p 127.0.0.1:9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.15.2
```

## Proof of Concept (current build) 
### API Endpoints (and scheduled background tasks)
- [ ] Fetch Latest Content From Elasticsearch (param: days_back)
### Scheduled scrape jobs
- [ ] Scrape Top Trending Tags for content -> Elasticsearch
	- [ ] Tweepy -> ES
- [ ] Perform Sentiment Analysis on content In Elasticsearch
	- [ ] query 30 mins back in ES
	- [ ] Score tweet text 
	- [ ] push updates to ES
### Streaming Aspirations
- [ ] Pulsar Function that performs sentiment analysis on content as it is streamed into pulsar topics
	- Need to research pulsar admin and how it works in production (Dockerfile/docker_run.sh?)

# API Blueprint
- Endpoints:
	- Query a user's home timeline (tweepy)
	- Fetch tweets by keyword (tweepy+elasticsearch keyword search): will also trigger crawling job
	- Get live tweets by tag:
		- Open a pulsar stream (or subscribe to existing stream) of tweets: utilizing WebSockets

Will likely need to use docker-compose.yml for easy launch of a local dev instance (pulsar and elasticsearch included)
