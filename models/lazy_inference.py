import os
from dotenv import load_dotenv
from config import settings
from services.openai_service import openai_client

# Load environment variables from .env file
# load_dotenv()

def optimize_prompt(prompt: str) -> str:
    """
    Optimize a user prompt using simple and efficient AI techniques.
    This lazy version uses straightforward optimization strategies.
    
    Args:
        prompt (str): The original prompt to optimize
        
    Returns:
        str: The optimized prompt
    """
    if openai_client is None:
        raise Exception("OpenAI client is not configured. Please set your OPENAI_API_KEY environment variable.")
    
    try:
        completion = openai_client.chat.completions.create(
            model=settings.LAZY_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"""Please rewrite this prompt to make it clearer and more effective:

{prompt}

Make it:
- More specific and detailed
- Easier to understand
- More likely to get a good response

Just give me the improved prompt:""",
                },
            ],
            max_tokens=settings.LAZY_MAX_TOKENS,
            temperature=settings.LAZY_TEMPERATURE,
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error optimizing prompt: {str(e)}")

# Interactive mode for direct execution
if __name__ == "__main__":
    print("----- LAZY inference request -----")
    prompt = input("Enter your prompt: ")
    
    try:
        optimized_prompt = optimize_prompt(prompt)
        print("Optimized prompt:", optimized_prompt)
    except Exception as e:
        print(f"Error: {e}")