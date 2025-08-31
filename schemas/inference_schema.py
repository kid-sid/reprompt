from pydantic import BaseModel
from enum import Enum

class InferenceType(str, Enum):
    LAZY = "lazy"
    PRO = "pro"

class InferenceRequest(BaseModel):
    prompt: str
    inference_type: InferenceType = InferenceType.LAZY
    max_tokens: int = 512

class InferenceResponse(BaseModel):
    output: str
    tokens_used: int
    inference_type: str
    model_used: str
