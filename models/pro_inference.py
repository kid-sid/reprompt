import os
from dotenv import load_dotenv
from config import settings
from services.openai_service import openai_client

def optimize_prompt(prompt: str) -> str:
    """
    Optimize a user prompt using advanced AI techniques for maximum effectiveness.
    This pro version uses more sophisticated prompting strategies.
    
    Args:
        prompt (str): The original prompt to optimize
        
    Returns:
        str: The optimized prompt
    """
    if openai_client is None:
        raise Exception("OpenAI client is not configured. Please set your OPENAI_API_KEY environment variable.")
    
    try:
        completion = openai_client.chat.completions.create(
            model=settings.PRO_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert prompt engineer with deep knowledge of AI optimization techniques. 
                    Your task is to transform user prompts using advanced strategies like:
                    - Chain-of-thought reasoning
                    - Few-shot learning patterns
                    - Role-based prompting
                    - Context window optimization
                    - Output format specification
                    - Constraint-based prompting
                    
                    Always maintain the original intent while significantly improving clarity, specificity, and effectiveness."""
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
            max_tokens=settings.MAX_TOKENS,
            temperature=settings.TEMPERATURE,
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error optimizing prompt: {str(e)}")

# Interactive mode for direct execution
if __name__ == "__main__":
    print("----- PRO inference request -----")
    prompt = input("Enter your prompt: ")
    
    try:
        optimized_prompt = optimize_prompt(prompt)
        print("Optimized prompt:", optimized_prompt)
    except Exception as e:
        print(f"Error: {e}")
