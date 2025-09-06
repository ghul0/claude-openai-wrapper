"""
Pydantic models for OpenAI Chat Completion API compatibility
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
import time
import uuid


class Message(BaseModel):
    """OpenAI message format"""
    role: Literal["system", "user", "assistant"]
    content: str


class ResponseFormat(BaseModel):
    """Response format specification"""
    type: Literal["text", "json_object"] = "text"


class ChatCompletionRequest(BaseModel):
    """OpenAI Chat Completion API request format"""
    model: str
    messages: List[Message]
    temperature: Optional[float] = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=4000, ge=1)
    response_format: Optional[ResponseFormat] = None
    stream: Optional[bool] = False
    n: Optional[int] = Field(default=1, ge=1, le=1)  # We only support n=1
    
    class Config:
        extra = "allow"  # Allow additional OpenAI parameters we don't use


class Choice(BaseModel):
    """Response choice"""
    index: int = 0
    message: Message
    finish_reason: Literal["stop", "length", "content_filter"] = "stop"


class Usage(BaseModel):
    """Token usage information"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    """OpenAI Chat Completion API response format"""
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4()}")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[Choice]
    usage: Usage = Field(default_factory=Usage)
    system_fingerprint: Optional[str] = None


class ErrorDetail(BaseModel):
    """Error detail for API errors"""
    message: str
    type: str
    param: Optional[str] = None
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """OpenAI API error response format"""
    error: ErrorDetail