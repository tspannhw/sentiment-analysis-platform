from pulsar import Function
import json
from streamer import score_tweets
import logging

logger = logging.getLogger(__name__)
# A function that demonstrates how to redirect logging to a topic.
# In this particular example, for every input string, the function
# does some logging. If --logTopic topic is specified, these log
# statements end up in that specified pulsar topic
class TweetScore(Function):
    def __init__(self):
        pass

    def process(self, input, context):
        context.get_logger().info(input)
        arr = json.loads(input)
        logger.info(f"Processed {input}")
        input = arr if type(arr) == list else list(arr)
        scored_tweets = score_tweets(input)
        return scored_tweets 


"""
bin/pulsar-admin functions localrun \
  --tenant public \
  --namespace default \
  --py /tmp/tweet_score_fn.zip \
  --classname TweetScore.TweetScore \
  --inputs persistent://public/default/raw_tweets \
  --output persistent://public/default/final_tweets \
  --log-topic persistent://public/default/log \
  --state-storage-service-url bk://127.0.0.1:4181
"""

