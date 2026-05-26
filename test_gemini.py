import os
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

async def test_gemini():
    print(f"Checking API Key...")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment variables.")
        return

    print(f"API Key found (length: {len(api_key)})")
    
    try:
        print("Initializing Gemini Client...")
        client = genai.Client(api_key=api_key)
        
        print("Listing 1.5 models...")
        for model in client.models.list():
            if "1.5" in model.name:
                print(f"- {model.name}")
            
        print("Sending test prompt to 'gemini-2.5-flash'...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Explain the importance of testing software in one sentence.'
        )
        
        print("\n--- Response from Gemini ---")
        print(response.text)
        print("----------------------------")
        print("SUCCESS: Gemini API is working correctly.")
        
    except Exception as e:
        print(f"\nERROR: Failed to generate content.")
        print(f"Details: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
