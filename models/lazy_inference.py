from config import settings
from services.openai_service import openai_client
from utils.helpers import handle_openai_error, sanitize_prompt, validate_prompt

def optimize_prompt(prompt: str) -> tuple[str, int]:
    """
    Optimize a user prompt using simple and efficient AI techniques.
    This lazy version uses straightforward optimization strategies.
    
    Args:
        prompt (str): The original prompt to optimize
        
    Returns:
        tuple[str, int]: The optimized prompt and tokens used
    """
    if openai_client is None:
        raise Exception("OpenAI client is not configured. Please set your OPENAI_API_KEY environment variable.")
    
    try:
        prompt = sanitize_prompt(prompt)
        if not prompt.strip():
            raise ValueError("Prompt can't be empty")
        if not validate_prompt(prompt):
            raise ValueError("Invalid prompt")
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
        
        optimized_prompt = completion.choices[0].message.content
        tokens_used = completion.usage.total_tokens if completion.usage else 0
        
        return optimized_prompt, tokens_used
    except ValueError as e:
        raise e
    except Exception as e:
        raise handle_openai_error(e)

# Interactive mode for direct execution
if __name__ == "__main__":
    print("----- LAZY inference request -----")
    prompt = input("Enter your prompt: ")
    
    try:
        optimized_prompt, tokens_used = optimize_prompt(prompt)
        print("Optimized prompt:", optimized_prompt)
        print("Tokens used:", tokens_used)
    except Exception as e:
        print(f"Error: {e}")