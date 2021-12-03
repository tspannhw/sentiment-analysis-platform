from pulsar import Function
import json
from ..elasticsearch import send_to_elasticsearch

# A function that demonstrates how to redirect logging to a topic.
# In this particular example, for every input string, the function
# does some logging. If --logTopic topic is specified, these log
# statements end up in that specified pulsar topic
class SentimentFetch(Function):
    def __init__(self):
        # self.tweet_topic = "non-persistent://public/default/tweets"
        pass

    def process(self, input, context):
        context.get_logger().info(input)
        # context.publish(self.tweet_topic, input)
        arr = json.loads(input)
        input = arr if type(arr) == list else list(arr)
        send_to_elasticsearch(input)
        return json.dumps(input)


"""
bin/pulsar-admin functions localrun \
  --tenant public \
  --namespace default \
  --py /tmp/sentiment_fetch_fn.zip \
  --classname SentimentFetch.SentimentFetch \
  --inputs persistent://public/default/input_tweets \
  --output persistent://public/default/published_tweets \
  --log-topic persistent://public/default/log \
  --state-storage-service-url bk://127.0.0.1:4181
"""

