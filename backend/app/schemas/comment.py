"""Comment schemas."""

from datetime import datetime

from pydantic import BaseModel


class CommentResponse(BaseModel):
    id: str
    document_id: str
    parent_id: str | None = None
    anchor_id: str | None = None
    provider: str
    external_id: str | None = None
    author: str | None = None
    content: str
    quote: str | None = None
    resolved: bool
    comment_scope: str = "general"
    section: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    content: str
    quote: str | None = None
    parent_id: str | None = None
    anchor_id: str | None = None
    comment_scope: str = "general"
    section: str | None = None


class CommentUpdate(BaseModel):
    resolved: bool | None = None
    comment_scope: str | None = None
    section: str | None = None


class ReplyGoogleCreate(BaseModel):
    comment_external_id: str
    content: str


class FeedbackItem(BaseModel):
    author: str
    content: str
    quote: str | None = None
    feedback_type: str = "general"  # general | structural | factual | editorial | methodological


class ImportFeedbackRequest(BaseModel):
    items: list[FeedbackItem]
    source: str = "email"  # email | document | meeting
