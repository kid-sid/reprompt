from config import settings
from services.openai_service import openai_client
from utils.helpers import handle_openai_error, sanitize_prompt, validate_prompt
from utils.prompt_loader import load_pro_prompt

def optimize_prompt(prompt: str) -> tuple[str, int]:
    """
    Optimize a user prompt using advanced AI techniques for maximum effectiveness.
    This pro version uses more sophisticated prompting strategies.
    
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
        # Load the pro prompt from file
        system_prompt = load_pro_prompt()
        
        completion = openai_client.chat.completions.create(
            model=settings.PRO_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"""Please analyze and optimize the following prompt using advanced prompting techniques:

ORIGINAL PROMPT:
{prompt}

REQUIREMENTS:
1. Maintain the core intent and purpose
2. Apply chain-of-thought reasoning where beneficial
3. Add specific constraints and context if missing
4. Optimize for the target AI model's capabilities
5. Include output format specifications if relevant
6. Use role-based prompting if applicable
7. Ensure the prompt is self-contained and clear

Please provide the optimized version:""",
                },
            ],
            max_tokens=settings.PRO_MAX_TOKENS,
            temperature=settings.PRO_TEMPERATURE,
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
    print("----- PRO inference request -----")
    prompt = input("Enter your prompt: ")
    
    try:
        optimized_prompt, tokens_used = optimize_prompt(prompt)
        print("Optimized prompt:", optimized_prompt)
        print("Tokens used:", tokens_used)
    except Exception as e:
        print(f"Error: {e}")
