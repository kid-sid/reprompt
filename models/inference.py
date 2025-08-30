import os
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()

def optimize_prompt(prompt: str) -> str:
    """
    Optimize a user prompt using AI to make it more efficient and effective.
    
    Args:
        prompt (str): The original prompt to optimize
        
    Returns:
        str: The optimized prompt
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt + "\n\nPlease rewrite the prompt in a more efficient way to get a proper response.",
                },
            ],
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error optimizing prompt: {str(e)}")

# Interactive mode for direct execution
if __name__ == "__main__":
    print("----- standard request -----")
    prompt = input("Enter your prompt: ")
    
    try:
        optimized_prompt = optimize_prompt(prompt)
        print("Optimized prompt:", optimized_prompt)
    except Exception as e:
        print(f"Error: {e}")