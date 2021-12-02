from elasticsearch import Elasticsearch
import logging

logger = logging.getLogger(__name__)
es = Elasticsearch()

def send_to_elasticsearch(data: list):
  logger.info("Bulk upsert to elasticsearch")
  