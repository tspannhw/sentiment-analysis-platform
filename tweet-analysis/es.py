from elasticsearch import Elasticsearch, helpers
from config import config
import logging
import datetime

logger = logging.getLogger(__name__)
es = Elasticsearch([config.es_url])
es.indices.create(index=config.tweet_index, ignore=400)


def wrap_tweet_for_es_insert(doc):
    return {
        "_id": doc.id,
        "updated_at": datetime.datetime.utcnow(),
        "created_at": doc.created_at,
        "_source": dict(doc),
    }


def send_to_elasticsearch(doc_generator, index: str):
    logger.info("Bulk upsert to elasticsearch")
    try:
        helpers.bulk(es, doc_generator(), index=index)
    except Exception as e:
        logger.exception(f"Bulk Upsert Error Elasticsearch")
        logger.error(e)
