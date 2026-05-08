from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentCreate(BaseModel):
    title: str
    category: str
    content: str
    metadata: Optional[dict] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[dict] = None


class DocumentResponse(BaseModel):
    id: str
    title: str
    category: str
    content: str
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    category: Optional[str] = None


class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    similarity: float
    category: str
