from tweet_analysis.config import config
from tweet_analysis.streamer import TwitterClient, TwitterStreamer
from elasticsearch import Elasticsearch, helpers
import logging
import pandas as pd
import datetime
from tweepy import Client, API, Stream, Paginator, OAuthHandler

logger = logging.getLogger(__name__)
es = Elasticsearch([config.es_url])
"""
# sample query
{
    "query": {
        "bool": {"must": {"exists": {"field": "analysis_nltk_compound"}}}
    },
    "sort": [ { "created_at" : "desc" }]
}
"""


def execute_search(query: dict, index=config.tweet_index, size=100000):
    """
    Returns generator of raw elasticsearch document.
    """
    docs = []
    for doc in helpers.scan(
        es, query=query, index=index, size=size, preserve_order=True
    ):
        docs.append(doc)
    return docs


def get_trending_tweets():
    return TwitterClient.get_trending_tweets()

