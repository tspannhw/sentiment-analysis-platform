from pydantic import BaseModel
from enum import Enum

class TweetCollectionType(Enum):
    RECENT: 1
    TRENDING: 2
    KEYWORD: 3

class TweetRequest(BaseModel):
    type: TweetCollectionType = TweetCollectionType.RECENT
    limit: int = 10000
    keyword: str = ""