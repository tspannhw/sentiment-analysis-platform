"""
Runner for all scraping jobs
"""
from streamer import TwitterClient
from es import wrap_tweet_for_es_insert, send_to_elasticsearch
from config import config
import logging

logger = logging.getLogger(__name__)


def index_recent_tweets():
    def _tweet_gen():
        tc = TwitterClient()
        recent_tweets = tc.get_recent_tweets(query="covid -is:retweet", num_tweets=30)
        for t in recent_tweets:
            yield wrap_tweet_for_es_insert(t)

    send_to_elasticsearch(_tweet_gen, config.tweet_index)


def sentiment_analysis():
    # query elasticsearch for recent tweets
    # send list of _source objects to analyze_tweets
    # send list of scored and updated tweets to index
    pass


if __name__ == "__main__":
    index_recent_tweets()

