from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import requests
from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)

# instantiate model
tokenizer = AutoTokenizer.from_pretrained(
    "nlptown/bert-base-multilingual-uncased-sentiment"
)
model = AutoModelForSequenceClassification.from_pretrained(
    "nlptown/bert-base-multilingual-uncased-sentiment"
)  # 665 MB


def calc_sentiment(text):
    # encode and calculate sentiment
    tokens = tokenizer.encode(
        f"{text}",
        return_tensors="pt",
    )
    # tokenizer.decode(tokens[0]) # decode
    result = model(
        tokens
    )  # returns SequenceClassifierOutput(loss, logits, grad_fn, hidden_states, attentions)
    max_result = int(torch.argmax(result.logits)) + 1  # get highest sentiment
    # logger.info(f"Test Review: 1/5 = {max_result}/5 stars")
    return max_result


# collect reviews


# load reviews into dataframe and score using model ^ .apply()
