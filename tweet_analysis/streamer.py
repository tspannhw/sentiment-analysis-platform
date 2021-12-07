from transformers.file_utils import DATASETS_IMPORT_ERROR
from tweepy import Client, API, Stream, Paginator, OAuthHandler
from config import config
from textblob import TextBlob
from bert_analysis import calc_sentiment
from nltk_parser import sia
import re
import logging
import coloredlogs
import json
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pulsar

plt.close("all")


def json_to_series(dct_series):
    keys, values = zip(*[item for item in dct_series.items()])
    return pd.Series(values, index=keys)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
coloredlogs.install(level="INFO")

AUTH = {
    "api_key": config.api_key,
    "api_key_secret": config.api_key_secret,
    "access_token": config.access_token,
    "access_token_secret": config.access_token_secret,
}


class TweetVisualizer:
    def plot_analysis_over_time(self, df, x_axis, y_axis):
        if type(y_axis) == list:
            for y in y_axis:
                plt.plot(df[x_axis], df[y], label=y)
        else:
            plt.plot(df[x_axis], df[y_axis], label=y_axis)
        plt.legend()
        plt.show()


class TweetAnalyzer:
    """
    Functionality for analyzing and categorizing content from tweets
    """

    def __init__(self, nltk_parser=sia):
        self.nltk_parser = nltk_parser

    def clean_tweet(self, tweet):
        return " ".join(
            re.sub(
                "(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet
            ).split()
        )

    def analyze_sentiment(self, tweet):
        analysis = TextBlob(self.clean_tweet(tweet))
        return self.normalize(analysis.sentiment.polarity)

    def analyze_content(self, tweet):
        return calc_sentiment(self.clean_tweet(tweet)) / 5

    def normalize(self, original_compound_score):
        # normalizes -1, 1 range to percentage
        if original_compound_score <= -0.0001:
            if original_compound_score <= 0:
                p = -1 - original_compound_score
                return abs(p)
        elif original_compound_score > 0.0001:
            if original_compound_score > 0:
                return float((0.5 + original_compound_score) / 1.5)
        else:
            return 0.5
        return 0.5

    def parse_nltk(self, tweet) -> dict:
        p = self.nltk_parser
        p_dict = p.polarity_scores(tweet)
        original_compound_score = p_dict["compound"]
        final_score = self.normalize(original_compound_score)
        p_dict["compound"] = final_score
        return p_dict

    def tweets_to_df(self, tweets):
        tweet_df = {}
        # set columns

        for t in tweets:
            if type(t) != dict:
                t = t.__dict__
            for k, _ in t.items():
                if (
                    "__" not in k
                    and (not k.startswith("_") or k == "_json")
                    and k not in tweet_df.keys()
                ):
                    tweet_df[k] = []

        for t in tweets:
            for k in tweet_df.keys():
                if type(t) != dict:
                    t = t.__dict__
                v = t.get(k, None)
                if "__" not in k and (not k.startswith("_") or k == "_json"):
                    if type(v) == dict:
                        d = {f"{k}_{ik}": iv for ik, iv in v.items()}
                        tweet_df[k].append(d)
                    elif (
                        type(v)
                        not in (dict, str, bool, list, int, float, datetime.datetime)
                        and v is not None
                    ):
                        v = v if type(v) == dict else v.__dict__
                        d = {f"{k}_{ik}": iv for ik, iv in v.items()}
                        tweet_df[k].append(d)
                    else:
                        tweet_df[k].append(v)

        df = pd.DataFrame.from_dict(tweet_df)
        return df


class TwitterClient:
    def __init__(self):
        self.client = Client(config.bearer_token)
        auth = OAuthHandler(config.api_key, config.api_key_secret)
        auth.set_access_token(config.access_token, config.access_token_secret)
        self.api = API(auth)

    def fetch_trending_tweets(self, trending_topic_count: int = 100):
        api = self.api
        resp = api.get_place_trends(1)  # global trends
        trends = resp[0]["trends"]
        tweets = []
        if trending_topic_count > len(trends):
            trending_topic_count = len(trends) - 1
        for trend in trends[:trending_topic_count]:
            query = trend["name"]
            tweets += self.get_recent_tweets(query)
        return tweets

    def get_recent_tweets(
        self, query: str = "covid -is:retweet", num_tweets: int = 10000
    ):
        tweets = []
        c = self.client
        for tweet in Paginator(
            c.search_recent_tweets,
            query=query,
            tweet_fields=config.tweet_fields,
            max_results=100,
        ).flatten(limit=num_tweets):
            if type(tweet.referenced_tweets) == list:
                tweet.referenced_tweets = len(tweet.get("referenced_tweets"))
            if tweet.author_id:
                user_id = tweet.author_id
                data = c.get_user(id=user_id)
                tweet.author_id = dict(data.data)
            tweets.append(tweet)
        return tweets

    def get_timeline_tweets(self, user, num_tweets: int = 10000):
        tweets = []
        user_client = self.client
        user = user_client.get_user(username="j__moussa")
        user_id = user.data.id
        for tweet in Paginator(
            self.client.get_users_tweets, user_id, max_results=num_tweets
        ).flatten(limit=num_tweets):
            tweets.append(tweet)
        return tweets


class TwitterStreamer:
    """
    Class for streaming and processing live tweets
    """

    def __init__(self):
        self.auth = AUTH

    def stream_tweets(self, output_file: str, filter_list: list):
        # this handles twitter authentication and connection to streaming api
        stream = TwitterListener(
            output_file,
            self.auth.api_key,
            self.auth.api_key_secret,
            self.auth.access_token,
            self.auth.access_token_secret,
        )
        # logger.info(f"Using default search terms ({filter_list})")
        stream.filter(track=filter_list)


class TwitterListener(Stream):
    """
    Basic tweet listener class that handles tweet processing
    """

    def __init__(self, output_file, *args, data_processing_fn=None):
        super(TwitterListener, self).__init__(*args)
        self.output_file = output_file
        self.data_processing_fn = data_processing_fn

    def on_data(self, data):
        # Data processing
        try:
            str_data = (
                data.decode("utf-8", "ignore").replace("\/", "/").replace("\\n", "")
            )
            # validate json
            data = json.loads(str_data)
            if self.data_processing_fn is not None:
                self.data_processing_fn(data)
                return True
            else:
                # upload to file
                with open(self.output_file, "a+") as fp:
                    fp.write(str_data + ",")
                return True

        except BaseException as e:
            logger.error(f"Invalid json parsing: {e}\n{str_data}")
        return True

    def on_error(self, status):
        if status == 420:
            return False
        logger.error(f"Error, status: {status}")


def analyze_tweets(tweet_docs: list):
    """
    Takes a list of tweet objects and scores them and returns the updated documents
    """
    analyzer = TweetAnalyzer()
    df = analyzer.tweets_to_df(tweet_docs)
    print(df)
    df["analysis_textblob"] = np.array(
        [analyzer.analyze_sentiment(tweet) for tweet in df["text"]]
    )
    for i in ("neg", "neu", "pos", "compound"):
        df[f"analysis_nltk_{i}"] = np.array(
            [analyzer.parse_nltk(tweet)[i] for tweet in df["text"]]
        )
    # Apply the function column wise to each column of interest
    # df = pd.concat([df, json_normalize(df["user"])], axis=1)
    print(
        df[
            [
                "id",
                "text",
                "analysis_textblob",
                "analysis_nltk_compound",
                "analysis_nltk_pos",
                "analysis_nltk_neu",
                "analysis_nltk_neg",
            ]
        ]
    )
    record_list = df.to_dict("records")

    return record_list


def analyze_user_timeline(user="j__moussa", home=False):
    t = TwitterClient()
    analyzer = TweetAnalyzer()
    api = t.api
    tweets = (
        api.user_timeline(screen_name=user, count=200)
        if not home
        else api.home_timeline(count=200)
    )
    df = analyzer.tweets_to_df(tweets)
    df["analysis_textblob"] = np.array(
        [analyzer.analyze_sentiment(tweet) for tweet in df["text"]]
    )
    # df["analysis_bert"] = np.array([analyzer.analyze_content(tweet) for tweet in df["text"]])
    for i in ("neg", "neu", "pos", "compound"):
        df[f"analysis_nltk_{i}"] = np.array(
            [analyzer.parse_nltk(tweet)[i] for tweet in df["text"]]
        )

    # Apply the function column wise to each column of interest
    # df = pd.concat([df, json_normalize(df["user"])], axis=1)
    final_df = pd.concat([df, df["user"].apply(json_to_series)], axis=1)
    final_df.drop("user", 1, inplace=True)
    print(
        final_df[
            [
                "text",
                "analysis_textblob",
                "analysis_nltk_compound",
                "analysis_nltk_pos",
                "analysis_nltk_neu",
                "analysis_nltk_neg",
            ]
        ]
    )
    print(final_df.describe())
    final_df.to_csv("./tweet_analysis.csv")
    record_list = final_df.to_dict("records")
    return record_list


def stream_tweets_by_keyword(keyword_search: list, filename="tweets.json"):
    """
    keyword search: list of keywords to filter tweets by
    filename: filename to write output to
    """
    client = pulsar.Client(config.pulsar_client_url)

    def _pulsar_producer(message: dict):
        producer = client.create_producer("persistent://public/default/input_tweets")
        producer.send(json.dumps(message).encode("utf8"))

    # Streaming data
    streamer = TwitterStreamer(data_processing_fn=_pulsar_producer)
    streamer.stream_tweets(filename, keyword_search)


def plot_sentiment_timeline(data_gen_func=None):
    recs = (
        analyze_user_timeline(home=True) if data_gen_func is None else data_gen_func()
    )
    df = pd.DataFrame.from_records(recs)
    viz = TweetVisualizer()
    viz.plot_analysis_over_time(
        df,
        "created_at",
        [
            "analysis_nltk_pos",
            "analysis_nltk_compound",
            "analysis_nltk_neg",
            "analysis_textblob",
        ],
    )


if __name__ == "__main__":
    plot_sentiment_timeline()
