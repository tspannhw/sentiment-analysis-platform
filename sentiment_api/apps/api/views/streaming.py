# -*- coding: utf-8 -*-
from typing import List

import logging
import json
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
from ..models.tweet import TweetRequest
from sentiment_api.apps.api.views.utils import execute_search, get_trending_tweets
import pulsar
from tweet_analysis.config import config


router = APIRouter()

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/ws/{topic}/{subscription}")
async def websocket_endpoint(websocket: WebSocket, topic: str, subscription: str):
    """
    Websocket connection to stream-in tweets.
    Under the hood: Start up pulsar consumer to pull in tweets based on the search query
    :query param: topic (kafka/pulsar topic)
    :query subscription: unique user_id to differentiate websocket session
    """
    # TODO: Abstract this to config
    client = pulsar.Client(config.pulsar_client_url)
    await manager.connect(websocket)
    try:
        consumer = client.subscribe(topic, subscription)
        while True:
            data = await websocket.receive_text()
            logger.info(f"WS Connected, {data}\nInitializing Pulsar Stream")
            # Start Pulsar consumer and consume messages back to API
            msg = consumer.receive()
            try:
                logger.info(
                    "Received message '{}' id='{}'".format(msg.data(), msg.message_id())
                )
                # Acknowledge successful processing of the message
                await manager.send_personal_message(msg.data(), websocket)
                consumer.acknowledge(msg)
            except:
                # Message failed to be processed
                consumer.negative_acknowledge(msg)
    except WebSocketDisconnect:
        client.close()
        manager.disconnect(websocket)


@router.get("/tweets")
async def fetch_tweets(req: TweetRequest) -> dict:
    # query elasticsearch for tweets based on Request
    logger.info(req)
    if req.type < 3:
        # non-keyword (fetch recent or trending)
        if req.type == 1:
            logger.info("Returning Most Recent Content")
            # most recent scored and sorted
            query = {
                "query": {
                    "bool": {"must": {"exists": {"field": "analysis_nltk_compound"}}}
                },
                "sort": [{"created_at": "desc"}],
            }
            docs = execute_search(query, size=req.limit)
        else:
            # results for tweets in top trending tags scored and sorted
            docs = get_trending_tweets()
            logger.info(
                f"Returning Trending Tweets (dictionary)\n{json.dumps(docs, indent=2)}"
            )
    else:
        # keyword search
        logger.info(f"Searching Tweets: '{req.keyword}'")
        query = {
            "query": {
                "bool": {
                    "must": {
                        "multi_match": {
                            "query": req.keyword,
                            "fields": ["text", "author_id.name", "author_id.username"],
                        }
                    }
                }
            },
            "sort": [{"created_at": "desc"}],
        }
        docs = execute_search(query, size=req.limit)
    return docs

