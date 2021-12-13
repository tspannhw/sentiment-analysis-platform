"""
Runner for all scraping jobs
"""
from types import WrapperDescriptorType
from streamer import TwitterClient, score_tweets
from es import es, wrap_tweet_for_es_insert, send_to_elasticsearch
from elasticsearch import helpers
from config import config
import logging

logger = logging.getLogger(__name__)


def index_recent_tweets(query="covid -is:retweet"):
    def _tweet_gen():
        tc = TwitterClient()
        recent_tweets = tc.get_recent_tweets(query=query, num_tweets=10000)
        for t in recent_tweets:
            yield wrap_tweet_for_es_insert(t)

    send_to_elasticsearch(_tweet_gen, config.tweet_index)


def sentiment_analysis():
    # query elasticsearch for recent tweets
    # send list of _source objects to score_tweets
    # send list of scored and updated tweets to index
    tweets = []
    for doc in helpers.scan(
        es,
        query={
            "query": {
                "bool": {"must_not": {"exists": {"field": "analysis_nltk_compound"}}}
            },
        },
        index="tweets",
        size=10000,
    ):
        tweet = doc["_source"]
        tweets.append(tweet)
    updated_tweets = score_tweets(tweets)
    for t in updated_tweets:
        yield wrap_tweet_for_es_insert(t)


def index_sentiment_analysis():
    send_to_elasticsearch(sentiment_analysis, config.tweet_index)


if __name__ == "__main__":
    index_recent_tweets()
    index_sentiment_analysis()

