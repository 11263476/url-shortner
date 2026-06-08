from pydantic import BaseModel, ConfigDict, HttpUrl, Field
from datetime import datetime
from typing import Optional, List


class WebhookCreate(BaseModel):
    url: HttpUrl = Field(..., description="Webhook callback URL that will receive POST events")
    events: List[str] = Field(..., min_length=1, description="List of event types to subscribe to (e.g. ['url.created', 'url.clicked'])")
    secret: str = Field(..., min_length=16, max_length=256, description="Webhook secret for HMAC signature verification")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "url": "https://hooks.example.com/callback",
            "events": ["url.created", "url.clicked"],
            "secret": "whsec_your_secret_here",
        }
    })


class WebhookUpdate(BaseModel):
    url: Optional[HttpUrl] = Field(None, description="New callback URL")
    events: Optional[List[str]] = Field(None, min_length=1, description="Replacement event subscriptions")
    secret: Optional[str] = Field(None, min_length=16, max_length=256, description="New HMAC secret")
    is_active: Optional[bool] = Field(None, description="Enable/disable the webhook")


class WebhookResponse(BaseModel):
    id: int
    workspace_id: int
    url: str
    events: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
