from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class InferenceType(str, Enum):
    LAZY = "lazy"
    PRO = "pro"

class InferenceRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=10000, description="The prompt to optimize")
    inference_type: InferenceType = InferenceType.LAZY
    max_tokens: Optional[int] = Field(None, ge=1, le=4000, description="Optional max tokens override")

class InferenceResponse(BaseModel):
    output: str = Field(..., description="The optimized prompt")
    tokens_used: int = Field(..., ge=0, description="Number of tokens used")
    inference_type: str = Field(..., description="The inference type used (lazy/pro)")
    model_used: str = Field(..., description="The model used for optimization")
    cached: bool = Field(False, description="Whether the result was served from cache")
    prompt_history_id: Optional[str] = Field(None, description="ID of the prompt history entry")
