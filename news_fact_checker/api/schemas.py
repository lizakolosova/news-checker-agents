from pydantic import BaseModel
from typing import Optional


class ArticleRequest(BaseModel):
    article_id: str
    title: Optional[str] = None
    text: str
    max_claims: int = 5