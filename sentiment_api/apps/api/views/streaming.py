# -*- coding: utf-8 -*-

import logging
from fastapi import WebSocket
from fastapi.routing import APIRouter
from ..models.tweet import TweetRequest
from utils import execute_search, get_trending_tweets

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/tweets")
async def fetch_tweets(req: TweetRequest):
    # query elasticsearch for tweets based on Request
    logger.info(req)
    if req.type < 3:
        # non-keyword (fetch recent or trending)
        if req.type == 1:
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
    else:
        # keyword search
        query = {
            "query": {
                "bool": {
                    "must": {
                        "multi_match": {
                            "query": TweetRequest.keyword,
                            "fields": ["text", "author_id.name", "author_id.username"],
                        }
                    }
                }
            },
            "sort": [{"created_at": "desc"}],
        }
        docs = execute_search(query, size=req.limit)
    return docs
