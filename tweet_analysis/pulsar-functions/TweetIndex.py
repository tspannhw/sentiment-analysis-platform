from pulsar import Function
import json
from ..es import send_to_elasticsearch

# A function that demonstrates how to redirect logging to a topic.
# In this particular example, for every input string, the function
# does some logging. If --logTopic topic is specified, these log
# statements end up in that specified pulsar topic
class TweetIndex(Function):
    def __init__(self):
        pass

    def process(self, input, context):
        context.get_logger().info(input)
        arr = json.loads(input)
        input = arr if type(arr) == list else list(arr)
        send_to_elasticsearch(input)
        return json.dumps(input)


"""
bin/pulsar-admin functions localrun \
  --tenant public \
  --namespace default \
  --py /tmp/tweet_index_fn.zip \
  --classname TweetIndex.TweetIndex \
  --inputs persistent://public/default/scored_tweets \
  --output persistent://public/default/es_tweets \
  --log-topic persistent://public/default/log \
  --state-storage-service-url bk://127.0.0.1:4181
"""

