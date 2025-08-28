from pydantic import BaseModel

class InferenceRequest(BaseModel):
    prompt: str
    max_tokens: int = 512

class InferenceResponse(BaseModel):
    output: str
    tokens_used: int
