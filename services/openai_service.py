import openai
from config import settings

def create_openai_client():
    """
    Create and return an OpenAI client with configured settings.
    
    Returns:
        openai.OpenAI: Configured OpenAI client instance
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API key is not configured. Please set OPENAI_API_KEY environment variable or create a .env file with your API key.")
    
    return openai.OpenAI(api_key=settings.OPENAI_API_KEY)

# Create a default client instance
try:
    openai_client = create_openai_client()
except ValueError as e:
    print(f"Warning: {e}")
    openai_client = None
